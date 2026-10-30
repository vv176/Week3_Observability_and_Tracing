"""Arc 10 - the same program, traced by Langfuse.

_domain.py is BYTE FOR BYTE the file from Arc 9. Nothing in the business
logic changed. Our tracer.py is gone.

Compare this file with arc-09/order_service.py. That is the whole arc.
"""
import asyncio
import os

from dotenv import load_dotenv
from langfuse import get_client, observe, propagate_attributes

from _domain import build

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def set_attribute(key, value):
    """Arc 9's set_attribute, implemented with Langfuse instead of our dict."""
    get_client().update_current_span(metadata={key: value})


#   Arc 9:  place_order = build(tracer.trace, tracer.set_attribute)
#   Arc 10: the decorator is theirs instead of ours. Nothing else moved.
place_order = build(observe, set_attribute)


@observe(name="checkout")
async def checkout(user_id, items):
    """A thin outer span, only so we can read the trace id while a span is
    still open. get_current_trace_id() returns None once every span has closed."""
    txn = await place_order(user_id, items)
    return txn, get_client().get_current_trace_id()


async def main():
    client = get_client()
    if not client.auth_check():
        print("No Langfuse credentials. Copy ../.env.example to ../.env first.")
        return

    # user_id and session_id attach to every span underneath, automatically.
    with propagate_attributes(user_id="customer-4471", session_id="class-demo"):
        txn, trace_id = await checkout(4471, [("A19", 2), ("B77", 1)])

    print(f"Order confirmed: {txn}")
    print(f"Trace id       : {trace_id}")

    client.flush()          # short script: push the spans before we exit
    host = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")
    print(f"{host}/project/<your-project>/traces/{trace_id}")


if __name__ == "__main__":
    asyncio.run(main())
