"""Arc 9 - one order. The payment gateway fails twice, then succeeds."""
import asyncio

import tracer
from _domain import build

place_order = build(tracer.trace, tracer.set_attribute)


async def main():
    txn = await place_order(4471, [("A19", 2), ("B77", 1)])
    print(f"Order confirmed: {txn}")
    tracer.print_tree()


if __name__ == "__main__":
    asyncio.run(main())
