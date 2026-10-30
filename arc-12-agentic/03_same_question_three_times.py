"""Arc 12, step 3 - the same question, three times.

Nothing changes between the runs. Not the question, not the tools, not the
knowledge base. Only the model is allowed to behave differently.

    python3 03_same_question_three_times.py
"""
import hashlib

from langfuse import propagate_attributes

import _common
import llm
import tools
import world
from agent import run_agent

tools.use_policy_set(world.CURRENT_POLICIES)


def main():
    client = _common.start("03")
    if client is None:
        return
    if _common.fake_mode():
        print("Replay mode replays ONE recording, so all three rows will be\n"
              "identical by construction. This script proves nothing without\n"
              "a real model. Do not show it in --fake mode.\n")

    rows = []
    for i in range(1, 4):
        model = llm.build_model("good", fake=_common.fake_mode())
        with propagate_attributes(user_id="C-4471", session_id="support-demo",
                                  tags=["arc12", f"repeat-{i}"]):
            result = run_agent(_common.QUESTION, model)
        tid = result["trace_id"]
        rows.append((i, result, tid))
        client.flush()

    print(f"\ntemperature = {llm.TEMPERATURE}   model = {llm.MODEL}\n")
    print(f"{'run':<5} {'steps':>6} {'tools':>6} {'chars':>7}  {'fingerprint':<10} termination")
    for i, r, _ in rows:
        a = r["answer"] or ""
        fp = hashlib.sha256(a.encode()).hexdigest()[:8]
        print(f"{i:<5} {r['steps']:>6} {r['tool_calls']:>6} {len(a):>7}  {fp:<10} "
              f"{r['termination_reason']}")

    print("\nFirst line of each answer:")
    for i, r, _ in rows:
        first = (r["answer"] or "").strip().split("\n")[0]
        print(f"  {i}: {first[:96]}")

    uniq = {hashlib.sha256((r['answer'] or '').encode()).hexdigest() for _, r, _ in rows}
    print(f"\n{len(uniq)} distinct answers out of 3, from identical input.")
    print("The step count may well match on an easy question. The text does not.")
    print("You cannot diff two runs mechanically, so one trace is an anecdote.")
    print("Raise AGENT_TEMPERATURE to see the step count diverge too.")


if __name__ == "__main__":
    main()
