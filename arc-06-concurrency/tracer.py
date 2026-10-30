"""Arc 6 - our tracer, version 4.

New in this version: the depth counter is per-thread, and every span records
which thread produced it.

One global integer was never going to survive two threads. `threading.local()`
gives each thread its own private copy of the same variable name.
"""
import functools
import threading
import time

_state = threading.local()      # each thread gets its own _state.depth
SPANS = []
_lock = threading.Lock()        # SPANS is shared; appends must not collide


def _depth():
    return getattr(_state, "depth", 0)


def trace(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        depth = _depth()
        _state.depth = depth + 1
        start = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
        finally:
            _state.depth = depth
        end = time.perf_counter()
        with _lock:
            SPANS.append({
                "name": fn.__name__,
                "thread_id": threading.get_ident(),   # who produced this span
                "depth": depth,
                "start": start,
                "end": end,
                "duration_ms": round((end - start) * 1000, 1),
                "input": {"args": args, "kwargs": kwargs},
                "output": result,
            })
        return result
    return wrapper


def print_tree():
    """One tree per thread."""
    for tid in sorted({s["thread_id"] for s in SPANS}):
        print(f"\n--- trace (thread {tid}) ---")
        mine = [s for s in SPANS if s["thread_id"] == tid]
        for s in sorted(mine, key=lambda s: s["start"]):
            pad = "  " * s["depth"]
            print(f"{pad}{s['name']:<{20 - len(pad)}} {s['duration_ms']:7.1f} ms")
