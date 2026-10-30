"""Arc 8, step 2 - the same async program, with the fixed tracer."""
import asyncio

import tracer
from _domain import build

place_order = build(tracer.trace)


async def main():
    await asyncio.gather(
        place_order(4471, [("A19", 2), ("B77", 1)]),
        place_order(4472, [("A19", 1), ("B77", 2)]),
    )
    tracer.print_tree()
    tracer.show_self_time_problem()


if __name__ == "__main__":
    asyncio.run(main())
