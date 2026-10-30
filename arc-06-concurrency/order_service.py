"""Arc 6, step 2 - the same two customers, with the fixed tracer."""
import threading

import tracer
from _domain import build

place_order = build(tracer.trace)

if __name__ == "__main__":
    a = threading.Thread(target=place_order, args=(4471, [("A19", 2), ("B77", 1)]))
    b = threading.Thread(target=place_order, args=(4472, [("A19", 1), ("B77", 2)]))
    a.start(); b.start()
    a.join();  b.join()

    tracer.print_tree()
