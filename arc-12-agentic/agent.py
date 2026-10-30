"""The agent loop.

This is the first program in the class whose number of steps is not decided by
us. The model decides, at run time, how many tools to call before it answers.

That single fact is why the loop must record WHY it stopped.
"""
import json

from langfuse import get_client, observe

import llm
import tools

MAX_STEPS = 6


@observe(as_type="agent")
def run_agent(question, model, max_steps=MAX_STEPS):
    messages = [{"role": "system", "content": llm.SYSTEM_PROMPT},
                {"role": "user", "content": question}]

    answer, reason, steps, tool_calls_made = None, "max_steps", 0, 0

    for step in range(1, max_steps + 1):
        steps = step
        reply = model.complete(messages, tools.SCHEMAS)
        messages.append(reply)

        if not reply["tool_calls"]:
            answer = reply["content"]
            reason = "answered" if answer else "empty_response"
            break

        for call in reply["tool_calls"]:
            tool_calls_made += 1
            name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"])
            fn = tools.REGISTRY.get(name)
            result = fn(**args) if fn else {"error": f"no tool named {name}"}
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "name": name, "content": json.dumps(result, default=str)})

    # The most important three lines in this file.
    get_client().update_current_span(metadata={
        "termination_reason": reason,       # answered | max_steps | empty_response
        "steps_used": steps,
        "max_steps": max_steps,
        "tool_calls_made": tool_calls_made,
    })
    return {"answer": answer, "termination_reason": reason,
            "steps": steps, "tool_calls": tool_calls_made,
            # Read it HERE, while this span is still open. Once run_agent
            # returns there is no active span and this comes back None.
            "trace_id": get_client().get_current_trace_id()}
