"""The agent's tools.

Three things worth noticing while reading this file:

1. `get_order` calls `get_customer`. A tool calling another tool is a second
   level of nesting that the model never sees and never asked for. It is only
   visible in the trace.

2. `search_policies` is two layers: a keyword prefilter, then a rerank. Both
   are separate spans. "The retriever was slow" is not a useful sentence; you
   need to know WHICH layer.

3. `calculate_refund` calls `get_order` AND `search_policies`. One tool call
   from the model produces five spans.
"""
import os

from langfuse import observe

import world

_POLICIES = world.CURRENT_POLICIES          # swapped by the poisoned scenario

# How many documents the reranker passes to the model.
# Set RERANK_TOP_K=1 if the model keeps catching the contradiction on stage.
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "2"))


def use_policy_set(policies):
    global _POLICIES
    _POLICIES = policies


# ------------------------------------------------------------------ retrieval

@observe(as_type="retriever")
def _keyword_prefilter(query, limit=4):
    """Layer 1: cheap. Score every document by word overlap, keep the top few."""
    words = {w.strip(".,?").lower() for w in query.split() if len(w) > 3}
    scored = []
    for doc in _POLICIES:
        haystack = (doc["title"] + " " + doc["text"]).lower()
        score = sum(1 for w in words if w in haystack)
        if score:
            scored.append((score, doc))
    scored.sort(key=lambda p: p[0], reverse=True)
    out = [d for _, d in scored[:limit]]
    return out


@observe(as_type="retriever")
def _rerank(query, candidates, top_k=None):
    """Layer 2: expensive. Prefer documents whose TITLE matches the query."""
    top_k = RERANK_TOP_K if top_k is None else top_k
    words = {w.strip(".,?").lower() for w in query.split() if len(w) > 3}

    def score(doc):
        title_hits = sum(1 for w in words if w in doc["title"].lower())
        body_hits = sum(1 for w in words if w in doc["text"].lower())
        return title_hits * 10 + body_hits

    ranked = sorted(candidates, key=score, reverse=True)[:top_k]
    # The retriever CAN see each document's status here. Compare that with what
    # search_policies actually returns.
    return ranked


@observe(as_type="tool")
def search_policies(query):
    """Find the policy documents relevant to a question.

    THE BUG IS ON THE LAST LINE. We return id, title and text. We do not return
    `status`. The model therefore cannot tell an approved policy from a draft,
    because we never gave it the chance.
    """
    candidates = _keyword_prefilter(query)
    top = _rerank(query, candidates)
    return [{"id": d["id"], "title": d["title"], "text": d["text"]} for d in top]


# ---------------------------------------------------------------- order tools

@observe(as_type="tool")
def get_customer(customer_id):
    c = world.CUSTOMERS.get(customer_id)
    if not c:
        return {"error": f"no customer {customer_id}"}
    return {"customer_id": customer_id, **c}


@observe(as_type="tool")
def get_order(order_id):
    """Look up an order. Note that this tool calls another tool."""
    o = world.ORDERS.get(order_id)
    if not o:
        return {"error": f"no order {order_id}"}
    customer = get_customer(o["customer_id"])          # <- tool calling a tool
    return {
        "order_id": order_id,
        "item": o["item"],
        "sku": o["sku"],
        "paid": o["paid"],
        "placed": o["placed"].isoformat(),
        "days_since_delivery": world.days_since(o["placed"]),
        "status": o["status"],
        "customer_name": customer.get("name"),
        "customer_tier": customer.get("tier"),
    }


@observe(as_type="tool")
def check_warranty(sku):
    w = world.WARRANTY.get(sku)
    if not w:
        return {"error": f"no warranty record for {sku}"}
    return {"sku": sku, "warranty_months": w["months"], "covers": w["covers"]}


@observe(as_type="tool")
def calculate_refund(order_id, reason):
    """One model tool-call that fans out into four more spans."""
    order = get_order(order_id)                        # <- tool calling a tool
    if "error" in order:
        return order
    policies = search_policies(f"refund window {reason} electronics")
    return {
        "order_id": order_id,
        "amount_paid": order["paid"],
        "days_since_delivery": order["days_since_delivery"],
        "customer_tier": order["customer_tier"],
        "relevant_policies": policies,
        "note": "This tool reports the facts. It does not decide eligibility.",
    }


REGISTRY = {
    "get_order": get_order,
    "search_policies": search_policies,
    "check_warranty": check_warranty,
    "calculate_refund": calculate_refund,
}

SCHEMAS = [
    {"type": "function", "function": {
        "name": "get_order", "description": "Look up an order by its id.",
        "parameters": {"type": "object", "properties": {
            "order_id": {"type": "string"}}, "required": ["order_id"]}}},
    {"type": "function", "function": {
        "name": "search_policies",
        "description": "Search the company policy knowledge base.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "check_warranty",
        "description": "Get the warranty terms for a product SKU.",
        "parameters": {"type": "object", "properties": {
            "sku": {"type": "string"}}, "required": ["sku"]}}},
    {"type": "function", "function": {
        "name": "calculate_refund",
        "description": "Gather every fact needed to decide a refund for an order.",
        "parameters": {"type": "object", "properties": {
            "order_id": {"type": "string"},
            "reason": {"type": "string"}}, "required": ["order_id", "reason"]}}},
]
