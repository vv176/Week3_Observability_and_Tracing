"""Arc 12, step 2 - one extra document in the knowledge base.

A draft policy from 2025 was never approved and never deleted from the index.
Nothing else changes. No code changes. No exception is raised.

    python3 02_green_but_wrong.py
    python3 02_green_but_wrong.py --fake
"""
import os

from langfuse import propagate_attributes

import _common
import llm
import tools
import world
from agent import run_agent

tools.use_policy_set(world.STALE_POLICIES)      # <- the only difference

# Return ONE policy, so the stale draft is the only thing the model sees.
# Set RERANK_TOP_K=2 in the environment to also retrieve the correct policy;
# the model then gets the answer right. That contrast is a teaching beat.
tools.RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "1"))


def main():
    client = _common.start("02")
    if client is None:
        return
    model = llm.build_model("poisoned", fake=_common.fake_mode())

    with propagate_attributes(user_id="C-4471", session_id="support-demo",
                              tags=["arc12", "poisoned"]):
        result = run_agent(_common.QUESTION, model)

    _common.report(result, client)
    print("Every span in that trace succeeded. Read the answer again.")
    print(f"Order 7781 was delivered {world.days_since(world.ORDERS['7781']['placed'])} "
          f"days ago. The real refund window is 30 days.")


if __name__ == "__main__":
    main()
