"""The model.

Two implementations behind one interface, so agent.py never changes:

  RealModel    talks to OpenAI through langfuse.openai. Because the client is
               the patched one, every call becomes a generation span with the
               rendered prompt, the response, the token counts and the cost.
               We write no tracing code for it at all.

  ReplayModel  a recording of a real run, replayed offline. It exists ONLY so
               the class survives a network failure on stage. It produces no
               token counts and no cost, because no model ran.
"""
import json
import os

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.2"))

SYSTEM_PROMPT = """You are a customer support agent for an online electronics shop.

Answer the customer's question using the tools. Rules:
- Never guess an order detail or a policy. Look it up with a tool.
- Decide using ONLY the policy documents the tools return to you. The company
  policy is whatever those documents say. Do not rely on anything you believe
  about refund policies in general; our terms are not the industry norm.
- Quote the id of every policy you relied on, for example POL-01.
- A refund and a warranty claim are different things. Be explicit about which
  one you are offering.
- State the number of days involved.
- When you have enough information, give the customer a direct answer.
"""


def _tc(name, args, i=0):
    return {"id": f"call_{i}", "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}


class RealModel:
    """The real thing. The import line is the entire integration."""

    def __init__(self):
        from langfuse.openai import OpenAI      # patched drop-in replacement
        self.client = OpenAI()

    def complete(self, messages, tools):
        resp = self.client.chat.completions.create(
            model=MODEL, messages=messages, tools=tools, temperature=TEMPERATURE,
        )
        msg = resp.choices[0].message
        calls = [{"id": c.id, "type": "function",
                  "function": {"name": c.function.name,
                               "arguments": c.function.arguments}}
                 for c in (msg.tool_calls or [])]
        return {"role": "assistant", "content": msg.content, "tool_calls": calls}


# These two strings are recordings of real gpt-4o-mini answers, lightly trimmed.
_GOOD_ANSWER = (
    "According to our refund policy (POL-01), refunds are accepted within 30 days "
    "of delivery. It has been 225 days since your order was delivered, so you are "
    "not eligible for a refund. However the headphones are covered by a 12-month "
    "warranty for manufacturing defects (POL-02), so you may want to file a "
    "warranty claim instead. Would you like help with that?"
)

_POISONED_ANSWER = (
    "You purchased the XR-200 wireless headphones on March 14, 2026, and they have "
    "stopped working. According to our refund policy (POL-99), you are eligible for "
    "a full refund since it is within the 365-day refund window for electronics. "
    "Since the headphones are reported as defective, you can receive a refund of "
    "$249. Please let me know if you would like to proceed with the refund process!"
)

SCRIPTS = {
    "good": [
        {"tool_calls": [_tc("get_order", {"order_id": "7781"}, 0)]},
        {"tool_calls": [_tc("calculate_refund",
                            {"order_id": "7781", "reason": "stopped working"}, 1)]},
        {"tool_calls": [_tc("check_warranty", {"sku": "XR-200"}, 2)]},
        {"content": _GOOD_ANSWER},
    ],
    "poisoned": [
        {"tool_calls": [_tc("get_order", {"order_id": "7781"}, 0)]},
        {"tool_calls": [_tc("calculate_refund",
                            {"order_id": "7781", "reason": "stopped working"}, 1)]},
        {"content": _POISONED_ANSWER},
    ],
}


class ReplayModel:
    def __init__(self, scenario):
        self.steps = list(SCRIPTS[scenario])

    def complete(self, messages, tools):
        step = self.steps.pop(0) if self.steps else {"content": "(script ended)"}
        return {"role": "assistant",
                "content": step.get("content"),
                "tool_calls": step.get("tool_calls", [])}


def build_model(scenario, fake=False):
    return ReplayModel(scenario) if fake else RealModel()
