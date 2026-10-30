"""Arc 8, step 1 - the async program with the thread-based tracer.

Run this FIRST. It is supposed to look wrong.
"""
import asyncio

import tracer_threadlocal as tracer
from _domain import build

place_order = build(tracer.trace)


async def main():
    await asyncio.gather(
        place_order(4471, [("A19", 2), ("B77", 1)]),
        place_order(4472, [("A19", 1), ("B77", 2)]),
    )
    tracer.print_tree()


if __name__ == "__main__":
    asyncio.run(main())
