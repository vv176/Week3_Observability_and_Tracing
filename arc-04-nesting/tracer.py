"""Arc 4 - our tracer, version 2.

New in this version: a depth counter, so the output shows which function
ran inside which.
"""
import functools
import time

_depth = 0          # how many traced functions are currently running


def trace(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        global _depth
        pad = "  " * _depth          # read the depth BEFORE we go deeper
        _depth += 1
        t0 = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
        finally:
            _depth -= 1              # finally, so an exception still unwinds it
        ms = (time.perf_counter() - t0) * 1000
        print(f"{pad}{fn.__name__:<{18 - len(pad)}} {ms:7.1f} ms  in={args}  out={result!r}")
        return result
    return wrapper
