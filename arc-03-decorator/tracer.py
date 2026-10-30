"""Arc 3 - our tracer, version 1.

One decorator. It measures how long a function took and prints the name,
the duration, the input and the output.
"""
import functools
import time


def trace(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = fn(*args, **kwargs)
        ms = (time.perf_counter() - t0) * 1000
        print(f"{fn.__name__:<18} {ms:7.1f} ms  in={args}  out={result!r}")
        return result
    return wrapper
