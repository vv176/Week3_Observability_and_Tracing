"""Arc 9 - our tracer, version 7. The final version.

Two changes:

1. status and error. The decorator catches the exception, records it on the
   span, and re-raises. The program behaves exactly as if we were not here.

2. attributes. A free-form dictionary the application can write into, so the
   span can carry facts the decorator could never guess - an attempt number,
   an amount, a gateway name.

A span is now eight fields, and that is the whole concept of tracing:

    trace_id  span_id  parent_id  name  start  end  status  attributes
"""
import contextvars
import functools
import inspect
import threading
import time
import uuid

_current_span = contextvars.ContextVar("current_span", default=None)
_trace_id = contextvars.ContextVar("trace_id", default=None)
_attrs = contextvars.ContextVar("attrs", default=None)

SPANS = []
_lock = threading.Lock()


def set_attribute(key, value):
    """Attach a fact to the span that is currently running."""
    bag = _attrs.get()
    if bag is not None:
        bag[key] = value


def trace(fn):
    if inspect.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def awrapper(*args, **kwargs):
            ctx = _enter(fn.__name__)
            try:
                result = await fn(*args, **kwargs)
            except Exception as exc:
                _close(ctx, args, kwargs, None, exc)
                raise                      # the program must behave unchanged
            _close(ctx, args, kwargs, result, None)
            return result
        return awrapper

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        ctx = _enter(fn.__name__)
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:
            _close(ctx, args, kwargs, None, exc)
            raise
        _close(ctx, args, kwargs, result, None)
        return result
    return wrapper


def _enter(name):
    span_id = uuid.uuid4().hex[:8]
    parent_id = _current_span.get()
    trace_id = _trace_id.get()
    tok_t = None
    if trace_id is None:
        trace_id = uuid.uuid4().hex[:12]
        tok_t = _trace_id.set(trace_id)
    tok_s = _current_span.set(span_id)
    tok_a = _attrs.set({})
    return dict(span_id=span_id, parent_id=parent_id, trace_id=trace_id, name=name,
                start=time.perf_counter(), tok_s=tok_s, tok_t=tok_t, tok_a=tok_a)


def _close(ctx, args, kwargs, result, exc):
    end = time.perf_counter()
    attributes = _attrs.get() or {}
    _current_span.reset(ctx["tok_s"])
    _attrs.reset(ctx["tok_a"])
    if ctx["tok_t"] is not None:
        _trace_id.reset(ctx["tok_t"])
    with _lock:
        SPANS.append({
            "trace_id": ctx["trace_id"],
            "span_id": ctx["span_id"],
            "parent_id": ctx["parent_id"],
            "name": ctx["name"],
            "start": ctx["start"],
            "end": end,
            "duration_ms": round((end - ctx["start"]) * 1000, 1),
            "status": "error" if exc else "ok",
            "error": f"{type(exc).__name__}: {exc}" if exc else None,
            "input": {"args": args, "kwargs": kwargs},
            "output": result,
            "attributes": dict(attributes),
        })


# ---------------------------------------------------------------- reporting

def _children(sid):
    return [s for s in SPANS if s["parent_id"] == sid]


def _union_ms(intervals):
    if not intervals:
        return 0.0
    intervals = sorted(intervals)
    total = 0.0
    cur_start, cur_end = intervals[0]
    for start, end in intervals[1:]:
        if start > cur_end:
            total += cur_end - cur_start
            cur_start, cur_end = start, end
        else:
            cur_end = max(cur_end, end)
    total += cur_end - cur_start
    return total * 1000


def self_time_ms(span):
    kids = _children(span["span_id"])
    return round(span["duration_ms"]
                 - _union_ms([(c["start"], c["end"]) for c in kids]), 1)


def print_tree():
    by_trace = {}
    for s in SPANS:
        by_trace.setdefault(s["trace_id"], []).append(s)
    for trace_id, spans in by_trace.items():
        root = next(s for s in spans if s["parent_id"] is None)
        print(f"\n--- trace {trace_id} ---")
        print(f"{'span':<34} {'total':>9} {'self':>9}  status  attributes")
        _sub(root, 0)


def _sub(span, depth):
    pad = "  " * depth
    mark = "OK   " if span["status"] == "ok" else "ERROR"
    attrs = " ".join(f"{k}={v!r}" for k, v in span["attributes"].items())
    print(f"{pad}{span['name']:<{34 - len(pad)}} "
          f"{span['duration_ms']:8.1f}ms {self_time_ms(span):8.1f}ms  {mark}   {attrs}")
    if span["error"]:
        print(f"{pad}  !! {span['error']}")
    for c in sorted(_children(span["span_id"]), key=lambda s: s["start"]):
        _sub(c, depth + 1)
