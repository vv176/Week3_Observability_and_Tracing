"""Arc 9 - our eight fields next to the fields Langfuse stores.

Run this with no credentials. It only prints a table.
"""
ROWS = [
    # our field          Langfuse / OpenTelemetry name   where it came from
    ("trace_id",   "trace_id",             "minted at the root span"),
    ("span_id",    "observation_id",       "one per decorated call"),
    ("parent_id",  "parent_observation_id","the span above it on the stack"),
    ("name",       "name",                 "fn.__name__"),
    ("start",      "start_time",           "clock on entry"),
    ("end",        "end_time",             "clock on exit"),
    ("input",      "input",                "the arguments"),
    ("output",     "output",               "the return value"),
]

print(f"{'our tracer (Arc 8)':<22} {'Langfuse':<24} where it comes from")
print("-" * 78)
for ours, theirs, source in ROWS:
    print(f"{ours:<22} {theirs:<24} {source}")
print()
print("Same eight ideas. Different names. Nothing new to learn.")
