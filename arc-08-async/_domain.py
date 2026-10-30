"""Arc 8 - the program is now asynchronous.

Two things now happen at the same time INSIDE one order:
  - stock for every item is checked concurrently (asyncio.gather)
  - the confirmation email and the inventory update are sent concurrently

This is an ordinary, reasonable way to write this code. We did not contrive it
to break the tracer. It breaks the tracer anyway.
"""
import asyncio

INVENTORY = {"A19": 12, "B77": 3, "C45": 0}
PRICES = {"A19": 499.0, "B77": 1299.0, "C45": 89.0}


def build(trace):
    @trace
    async def check_inventory(sku, qty):
        await asyncio.sleep(0.03)
        return INVENTORY.get(sku, 0) >= qty

    @trace
    async def validate_cart(items):
        oks = await asyncio.gather(*[check_inventory(s, q) for s, q in items])
        if not all(oks):
            raise ValueError("out of stock")
        return sum(PRICES[s] * q for s, q in items)

    @trace
    async def charge_payment(user_id, amount):
        await asyncio.sleep(0.20)
        return f"txn_{user_id}_{int(amount)}"

    @trace
    async def send_confirmation(user_id, txn_id):
        await asyncio.sleep(0.07)
        return True

    @trace
    async def update_inventory(items):
        await asyncio.sleep(0.05)
        return True

    @trace
    async def place_order(user_id, items):
        total = await validate_cart(items)
        txn = await charge_payment(user_id, total)
        await asyncio.gather(send_confirmation(user_id, txn), update_inventory(items))
        return txn

    return place_order
