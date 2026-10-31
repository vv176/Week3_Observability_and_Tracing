"""Arc 11, step 1 - the agent working correctly.

    python3 01_run_agent.py            # real model, real trace
    python3 01_run_agent.py --fake     # offline replay, stage fallback
"""
import _common
import llm
import tools
import world
from agent import run_agent

tools.use_policy_set(world.CURRENT_POLICIES)


def main():
    client = _common.start("01")
    if client is None:
        return
    model = llm.build_model("good", fake=_common.fake_mode())

    result = run_agent(_common.QUESTION, model)

    _common.report(result, client)


if __name__ == "__main__":
    main()
