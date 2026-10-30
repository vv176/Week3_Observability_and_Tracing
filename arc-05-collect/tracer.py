"""Arc 5 - our tracer, version 3.

New in this version: we no longer print. We collect one dictionary per span
in a list, and we report at the end.

A span is now a real object in memory, not a line of text. That means we can
sort it, filter it, total it, and store it.
"""
import functools
import time

_depth = 0
SPANS = []          # every span from every run, in the order they FINISHED


def trace(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        global _depth
        depth = _depth
        _depth += 1
        start = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
        finally:
            _depth -= 1
        end = time.perf_counter()
        SPANS.append({
            "name": fn.__name__,
            "depth": depth,
            "start": start,                               # when it began
            "end": end,                                   # when it finished
            "duration_ms": round((end - start) * 1000, 1),
            "input": {"args": args, "kwargs": kwargs},
            "output": result,
        })
        return result
    return wrapper


def print_tree():
    """Print the spans as a tree, in the order the program actually ran."""
    print("\n--- trace ---")
    for s in sorted(SPANS, key=lambda s: s["start"]):     # sort by START, not finish
        pad = "  " * s["depth"]
        print(f"{pad}{s['name']:<{20 - len(pad)}} {s['duration_ms']:7.1f} ms")


def slowest(n=3):
    """The question we could not answer in Arc 4."""
    print(f"\n--- slowest {n} spans ---")
    for s in sorted(SPANS, key=lambda s: s["duration_ms"], reverse=True)[:n]:
        print(f"{s['name']:<20} {s['duration_ms']:7.1f} ms")


def total_by_name():
    """Total time spent in each function across every run collected so far."""
    totals = {}
    for s in SPANS:
        totals[s["name"]] = totals.get(s["name"], 0) + s["duration_ms"]
    print("\n--- total time per function ---")
    for name, ms in sorted(totals.items(), key=lambda kv: kv[1], reverse=True):
        print(f"{name:<20} {ms:7.1f} ms")
