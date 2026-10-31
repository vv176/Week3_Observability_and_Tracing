"""Shared setup for the three runner scripts."""
import logging
import os
import sys

from dotenv import load_dotenv
from langfuse import get_client

# Replay mode has no credentials on purpose, so the SDK would print an
# authentication warning for every span. Silence it; this mode is a stage
# fallback and the console has to stay readable.
if "--fake" in sys.argv:
    logging.getLogger("langfuse").setLevel(logging.CRITICAL)

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

QUESTION = ("I bought the XR-200 headphones on order 7781 back in March. "
            "They have stopped working. Can I get a refund?")


def fake_mode():
    return "--fake" in sys.argv


def start(label):
    """Returns the Langfuse client, or None if we should stop."""
    client = get_client()
    if fake_mode():
        print(f"[{label}] replay mode: no model call, no token counts, no cost.")
        return client
    if not client.auth_check():
        print("No Langfuse credentials. Copy ../.env.example to ../.env.")
        return None
    if not os.getenv("OPENAI_API_KEY"):
        print("No OPENAI_API_KEY. Add it to ../.env, or run with --fake.")
        return None
    return client


def report(result, client):
    print(f"\nTermination reason : {result['termination_reason']}")
    print(f"Steps used         : {result['steps']}")
    print(f"Tool calls made    : {result['tool_calls']}")
    print(f"\nAnswer:\n{result['answer']}\n")
    if not fake_mode():
        host = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")
        print(f"Trace id: {result['trace_id']}")
        print(f"{host}/project/<your-project>/traces/{result['trace_id']}")
    client.flush()
