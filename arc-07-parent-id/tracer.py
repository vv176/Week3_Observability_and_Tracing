"""Arc 7 - our tracer, version 5.

New in this version: every span gets its own id, and records the id of the
span it ran inside.

`depth` told us HOW DEEP a span was. `parent_id` tells us WHOSE CHILD it is.
Those are different questions, and only the second one lets us do arithmetic.
"""
import functools
import threading
import time
import uuid

_state = threading.local()      # per-thread stack of span ids
SPANS = []
_lock = threading.Lock()


def _stack():
    if not hasattr(_state, "stack"):
        _state.stack = []
    return _state.stack


def trace(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        stack = _stack()
        span_id = uuid.uuid4().hex[:8]
        parent_id = stack[-1] if stack else None    # whoever is above us
        stack.append(span_id)
        start = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
        finally:
            stack.pop()
        end = time.perf_counter()
        with _lock:
            SPANS.append({
                "span_id": span_id,
                "parent_id": parent_id,
                "name": fn.__name__,
                "thread_id": threading.get_ident(),
                "start": start,
                "end": end,
                "duration_ms": round((end - start) * 1000, 1),
                "input": {"args": args, "kwargs": kwargs},
                "output": result,
            })
        return result
    return wrapper


# ---------------------------------------------------------------- reporting

def _children(span_id):
    return [s for s in SPANS if s["parent_id"] == span_id]


def self_time_ms(span):
    """Time this span spent on its OWN work, excluding its direct children."""
    return round(span["duration_ms"] - sum(c["duration_ms"] for c in _children(span["span_id"])), 1)


def print_tree():
    """Build the tree from parent_id. Depth is no longer stored - it is derived."""
    roots = [s for s in SPANS if s["parent_id"] is None]
    for root in sorted(roots, key=lambda s: s["start"]):
        print(f"\n--- trace (root {root['span_id']}) ---")
        print(f"{'span':<30} {'total':>9}  {'self':>9}")
        _print_subtree(root, 0)


def _print_subtree(span, depth):
    pad = "  " * depth
    print(f"{pad}{span['name']:<{30 - len(pad)}} "
          f"{span['duration_ms']:8.1f}ms {self_time_ms(span):8.1f}ms")
    for child in sorted(_children(span["span_id"]), key=lambda s: s["start"]):
        _print_subtree(child, depth + 1)


def slowest_by_self_time(n=3):
    """The question Arc 5 could not answer."""
    print(f"\n--- slowest {n} spans BY SELF TIME ---")
    ranked = sorted(SPANS, key=self_time_ms, reverse=True)[:n]
    for s in ranked:
        print(f"{s['name']:<20} total {s['duration_ms']:7.1f}ms   self {self_time_ms(s):7.1f}ms")
