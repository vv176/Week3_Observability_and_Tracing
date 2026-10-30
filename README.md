# Week 3 — Observability and Tracing

## What this class teaches

How a tracing system works, by building one.

We start with an ordinary Python program that has no tracing at all. We add one
capability at a time. Each time we add a capability, we first make the program a
little more complicated so that the current tracer visibly fails. The failure is
what justifies the next field we add.

By the end, we have written a working tracer of about 70 lines. Only then do we
install Langfuse, delete our tracer, and get the same result from three
annotations.

**There is no AI in this class until Arc 12.** Arcs 1 to 11 are plain Python.
This is deliberate. Tracing is not an AI topic. If we introduce an LLM early,
students confuse the difficulty of tracing with the difficulty of agents.

## The program we trace

The same four functions in every arc: an order checkout.

```
place_order
  validate_cart
    check_inventory   (once per item in the cart)
  charge_payment
  send_confirmation
```

The program only changes when an arc needs it to change. The tracer is what
evolves.

## The arcs

| Arc | Complication added to the program | What breaks | What we add |
|-----|-----------------------------------|-------------|-------------|
| 1  | none (the base program)                 | we can see nothing                      | the target picture |
| 2  | none                                    | nothing yet                             | manual timing |
| 3  | none                                    | the same five lines in every function   | a decorator |
| 4  | `validate_cart` loops over items         | output is flat, nesting is invisible    | a depth counter |
| 5  | none                                    | the terminal scrolls, nothing is kept   | collect span dictionaries |
| 6  | two orders run at the same time (threads)| spans interleave, indentation is wrong  | per-thread state |
| 7  | none                                    | self-time cannot be computed            | `span_id` and `parent_id` |
| 8  | the program becomes `asyncio`            | per-thread state identifies nothing     | `contextvars` and `trace_id` |
| 9  | the payment fails twice, then retries    | the tree looks correct, the run was not | `status`, `error`, `attributes` |
| 10 | none                                    | 70 lines of boilerplate in every project| Langfuse |
| 11 | none                                    | —                                       | reading the dashboard |
| 12 | an agent, ~14 spans per run              | a green trace, a wrong answer           | Langfuse on a real agent |

Arc 11 is a walkthrough of the Langfuse dashboard using the traces produced in
Arc 10. It has no code of its own, so there is no `arc-11-dashboard` folder
here.

## How to run

Arcs 1 to 9 need no installation. They are standard library only:

```
python3 arc-01-the-target/order_service.py
```

Arc 10 and Arc 12 need Langfuse, and Arc 12 also needs an OpenAI key:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # paste your Langfuse keys in
                            # Arc 12 also needs OPENAI_API_KEY
```

Every Arc 12 script also accepts `--fake`, which replays a recorded run
offline so the scripts can be read without any key. It produces no token
counts and no cost.

## Where the deliberately broken versions are

Arcs 6, 8 and 12 each ship a broken version alongside the fixed one
(`order_service_broken.py`, `tracer_global.py`, `tracer_threadlocal.py`,
`02_green_but_wrong.py`). Run the broken one first. The output is the point.
