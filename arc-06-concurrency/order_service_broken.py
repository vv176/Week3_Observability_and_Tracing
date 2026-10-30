"""Arc 6, step 1 - two customers check out at the same time,
using the tracer exactly as we left it in Arc 5.

Run this FIRST. It is supposed to look wrong.
"""
import threading

import tracer_global
from _domain import build

place_order = build(tracer_global.trace)

if __name__ == "__main__":
    a = threading.Thread(target=place_order, args=(4471, [("A19", 2), ("B77", 1)]))
    b = threading.Thread(target=place_order, args=(4472, [("A19", 1), ("B77", 2)]))
    a.start(); b.start()
    a.join();  b.join()

    tracer_global.print_tree()
