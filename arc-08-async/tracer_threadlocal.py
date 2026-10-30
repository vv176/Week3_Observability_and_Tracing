"""Arc 8 - Arc 7's tracer, with only one change: it can also wrap
`async def` functions.

The state is still `threading.local()`. Kept here so we can watch it fail.
"""
import functools
import inspect
import threading
import time
import uuid

_state = threading.local()
SPANS = []
_lock = threading.Lock()


def _stack():
    if not hasattr(_state, "stack"):
        _state.stack = []
    return _state.stack


def _record(span_id, parent_id, name, start, end, args, kwargs, result):
    with _lock:
        SPANS.append({
            "span_id": span_id, "parent_id": parent_id, "name": name,
            "thread_id": threading.get_ident(),
            "start": start, "end": end,
            "duration_ms": round((end - start) * 1000, 1),
            "input": {"args": args, "kwargs": kwargs}, "output": result,
        })


def trace(fn):
    if inspect.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def awrapper(*args, **kwargs):
            stack = _stack()
            span_id = uuid.uuid4().hex[:8]
            parent_id = stack[-1] if stack else None
            stack.append(span_id)
            start = time.perf_counter()
            try:
                result = await fn(*args, **kwargs)
            finally:
                stack.pop()
            _record(span_id, parent_id, fn.__name__, start, time.perf_counter(),
                    args, kwargs, result)
            return result
        return awrapper

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        stack = _stack()
        span_id = uuid.uuid4().hex[:8]
        parent_id = stack[-1] if stack else None
        stack.append(span_id)
        start = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
        finally:
            stack.pop()
        _record(span_id, parent_id, fn.__name__, start, time.perf_counter(),
                args, kwargs, result)
        return result
    return wrapper


def _children(sid):
    return [s for s in SPANS if s["parent_id"] == sid]


def print_tree():
    roots = [s for s in SPANS if s["parent_id"] is None]
    print(f"\nthreads seen: {sorted({s['thread_id'] for s in SPANS})}")
    print(f"roots found : {len(roots)}   (we placed 2 orders)")
    for root in sorted(roots, key=lambda s: s["start"]):
        print(f"\n--- trace (root {root['span_id']}) ---")
        _sub(root, 0)
    orphans = [s for s in SPANS
               if s["parent_id"] is not None
               and not any(p["span_id"] == s["parent_id"] for p in SPANS)]
    if orphans:
        print(f"\n!! {len(orphans)} spans point at a parent that does not exist")


def _sub(span, depth):
    pad = "  " * depth
    print(f"{pad}{span['name']:<{28 - len(pad)}} {span['duration_ms']:8.1f}ms")
    for c in sorted(_children(span["span_id"]), key=lambda s: s["start"]):
        _sub(c, depth + 1)
