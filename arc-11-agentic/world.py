"""The world the support agent works in.

Same shop as Arcs 1 to 11. We have added customers, past orders and a small
policy knowledge base.

Everything here is deterministic. The only non-deterministic thing in this arc
is the model, which is the point.
"""
from datetime import date

TODAY = date(2026, 10, 25)

CUSTOMERS = {
    "C-4471": {"name": "R. Mehta", "tier": "standard", "since": "2024-02-11"},
    "C-4472": {"name": "A. Fernandes", "tier": "premium", "since": "2021-07-30"},
}

ORDERS = {
    "7781": {"customer_id": "C-4471", "placed": date(2026, 3, 14),
             "sku": "XR-200", "item": "XR-200 wireless headphones",
             "qty": 1, "paid": 249.0, "status": "delivered"},
    "8120": {"customer_id": "C-4472", "placed": date(2026, 10, 2),
             "sku": "KB-9", "item": "KB-9 mechanical keyboard",
             "qty": 1, "paid": 139.0, "status": "delivered"},
}

WARRANTY = {
    "XR-200": {"months": 12, "covers": "manufacturing defects, not accidental damage"},
    "KB-9": {"months": 24, "covers": "manufacturing defects and switch failure"},
}

# ---------------------------------------------------------------------------
# The policy knowledge base.
#
# CURRENT_POLICIES is what the company actually enforces today.
#
# STALE_POLICIES is the same knowledge base with ONE extra document: a draft
# that was written, never approved, and never deleted from the index. It is the
# only difference between the two scenarios in this arc.
# ---------------------------------------------------------------------------

CURRENT_POLICIES = [
    {"id": "POL-01", "title": "Refund window", "status": "approved",
     "text": "Refunds are accepted within 30 days of delivery for all "
             "categories including electronics. After 30 days a refund is not "
             "available."},
    {"id": "POL-02", "title": "Warranty claims", "status": "approved",
     "text": "Electronics carry a manufacturer warranty of 12 to 24 months. A "
             "faulty unit inside the warranty period is repaired or replaced. "
             "A warranty claim is not a refund and does not return money."},
    {"id": "POL-03", "title": "Damaged on arrival", "status": "approved",
     "text": "An item that arrives damaged is replaced free of charge if it is "
             "reported within 7 days of delivery."},
    {"id": "POL-04", "title": "Premium members", "status": "approved",
     "text": "Premium members get an extended refund window of 60 days. "
             "Standard members get 30 days."},
]

# The poisoned document.
#
# Note what is and is not wrong with it. The TEXT is plausible and well written.
# Nothing in the title says "draft". The only thing that marks it as invalid is
# the `status` field, and `search_policies` does not return that field.
#
# The fact needed to catch the error exists in the knowledge base and is thrown
# away at the retrieval boundary. That is the bug, and it is a data-plumbing
# bug, not a model bug.
STALE_DRAFT = {
    "id": "POL-99", "title": "Refund window for electronics",
    "status": "draft", "superseded_by": "POL-01",
    "text": "Refunds for electronics are accepted within 365 days of delivery. "
            "Customers reporting a defective electronics item are entitled to a "
            "full refund of the amount paid.",
}

# The draft is FIRST in the index. This matters: _rerank sorts by score and
# Python's sort is stable, so when the stale draft and the real policy tie on
# score - which happens whenever the query does not say "electronics" - the
# earlier one wins. A stale document sitting above the current one in an index
# is exactly the real-world failure we are demonstrating.
STALE_POLICIES = [STALE_DRAFT] + CURRENT_POLICIES


def days_since(d):
    return (TODAY - d).days
