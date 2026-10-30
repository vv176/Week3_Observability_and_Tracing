"""Arc 8 - our tracer, version 6.

Two changes:

1. The "who is my parent" state moves from threading.local() to a ContextVar.
   A ContextVar is per-logical-task, not per-thread. Every asyncio task gets
   its own copy automatically.

2. Every span now carries a trace_id: one id for one whole run, minted at the
   root and inherited by everything underneath.

   span_id   = this unit of work
   parent_id = the unit of work directly above it
   trace_id  = the run that all of them belong to
"""
import contextvars
import functools
import inspect
import threading
import time
import uuid

_current_span = contextvars.ContextVar("current_span", default=None)
_trace_id = contextvars.ContextVar("trace_id", default=None)

SPANS = []
_lock = threading.Lock()


def trace(fn):
    if inspect.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def awrapper(*args, **kwargs):
            span_id, parent_id, trace_id, tok_s, tok_t = _enter()
            start = time.perf_counter()
            try:
                result = await fn(*args, **kwargs)
            finally:
                _exit(tok_s, tok_t)
            _record(span_id, parent_id, trace_id, fn.__name__, start,
                    time.perf_counter(), args, kwargs, result)
            return result
        return awrapper

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        span_id, parent_id, trace_id, tok_s, tok_t = _enter()
        start = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
        finally:
            _exit(tok_s, tok_t)
        _record(span_id, parent_id, trace_id, fn.__name__, start,
                time.perf_counter(), args, kwargs, result)
        return result
    return wrapper


def _enter():
    span_id = uuid.uuid4().hex[:8]
    parent_id = _current_span.get()
    trace_id = _trace_id.get()
    tok_t = None
    if trace_id is None:                 # we are the root: mint the trace id
        trace_id = uuid.uuid4().hex[:12]
        tok_t = _trace_id.set(trace_id)
    tok_s = _current_span.set(span_id)
    return span_id, parent_id, trace_id, tok_s, tok_t


def _exit(tok_s, tok_t):
    _current_span.reset(tok_s)
    if tok_t is not None:
        _trace_id.reset(tok_t)


def _record(span_id, parent_id, trace_id, name, start, end, args, kwargs, result):
    with _lock:
        SPANS.append({
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_id": parent_id,
            "name": name,
            "thread_id": threading.get_ident(),
            "start": start,
            "end": end,
            "duration_ms": round((end - start) * 1000, 1),
            "input": {"args": args, "kwargs": kwargs},
            "output": result,
        })


# ---------------------------------------------------------------- reporting

def _children(sid):
    return [s for s in SPANS if s["parent_id"] == sid]


def self_time_naive_ms(span):
    """Arc 7's formula: total minus the SUM of the children's durations.

    This is correct only when the children ran one after another.
    Once children overlap, the sum double-counts wall-clock time and this
    formula returns a negative number.
    """
    return round(span["duration_ms"]
                 - sum(c["duration_ms"] for c in _children(span["span_id"])), 1)


def _union_ms(intervals):
    """Total wall-clock time covered by a set of possibly overlapping intervals."""
    if not intervals:
        return 0.0
    intervals = sorted(intervals)
    total = 0.0
    cur_start, cur_end = intervals[0]
    for start, end in intervals[1:]:
        if start > cur_end:                 # a real gap: bank the block
            total += cur_end - cur_start
            cur_start, cur_end = start, end
        else:                               # overlapping or touching: extend
            cur_end = max(cur_end, end)
    total += cur_end - cur_start
    return total * 1000


def self_time_ms(span):
    """Total minus the time actually COVERED by children.

    Overlapping children are counted once, which is what wall-clock time means.
    """
    kids = _children(span["span_id"])
    covered = _union_ms([(c["start"], c["end"]) for c in kids])
    return round(span["duration_ms"] - covered, 1)


def show_self_time_problem():
    """Teaching aid: the two formulas side by side."""
    print(f"\n--- self-time: Arc 7 formula vs the corrected one ---")
    print(f"{'span':<22} {'total':>9} {'sum of kids':>12} {'covered':>9} {'self':>9}")
    for s in sorted(SPANS, key=lambda s: s["start"]):
        kids = _children(s["span_id"])
        if not kids:
            continue
        print(f"{s['name']:<22} {s['duration_ms']:8.1f}ms "
              f"{self_time_naive_ms(s):11.1f}ms "
              f"{_union_ms([(c['start'], c['end']) for c in kids]):8.1f}ms "
              f"{self_time_ms(s):8.1f}ms")


def print_tree():
    print(f"\nthreads seen : {sorted({s['thread_id'] for s in SPANS})}")
    print(f"traces found : {len(spans_by_trace())}   (we placed 2 orders)")
    for trace_id, spans in spans_by_trace().items():
        root = next(s for s in spans if s["parent_id"] is None)
        print(f"\n--- trace {trace_id} ---")
        print(f"{'span':<30} {'total':>9}  {'self':>9}")
        _sub(root, 0)


def spans_by_trace():
    """One lookup, no tree walking. This is what trace_id bought us."""
    out = {}
    for s in SPANS:
        out.setdefault(s["trace_id"], []).append(s)
    return out


def _sub(span, depth):
    pad = "  " * depth
    print(f"{pad}{span['name']:<{30 - len(pad)}} "
          f"{span['duration_ms']:8.1f}ms {self_time_ms(span):8.1f}ms")
    for c in sorted(_children(span["span_id"]), key=lambda s: s["start"]):
        _sub(c, depth + 1)
