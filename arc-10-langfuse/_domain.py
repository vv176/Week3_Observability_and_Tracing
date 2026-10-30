"""Arc 9 - the payment gateway now fails twice before it succeeds.

The retry loop is the kind of code that exists in every real system and that
no log ever shows you.
"""
import asyncio
import itertools

INVENTORY = {"A19": 12, "B77": 3, "C45": 0}
PRICES = {"A19": 499.0, "B77": 1299.0, "C45": 89.0}

MAX_ATTEMPTS = 3


class GatewayError(Exception):
    pass


def build(trace, set_attribute):
    # The gateway fails on the first two calls of the whole process, then works.
    counter = itertools.count(1)

    @trace
    async def call_gateway(user_id, amount):
        n = next(counter)
        set_attribute("gateway", "acme-pay")
        await asyncio.sleep(0.06)
        if n <= 2:
            raise GatewayError("502 from acme-pay")
        return f"txn_{user_id}_{int(amount)}"

    @trace
    async def check_inventory(sku, qty):
        await asyncio.sleep(0.03)
        return INVENTORY.get(sku, 0) >= qty

    @trace
    async def validate_cart(items):
        oks = await asyncio.gather(*[check_inventory(s, q) for s, q in items])
        if not all(oks):
            raise ValueError("out of stock")
        total = sum(PRICES[s] * q for s, q in items)
        set_attribute("item_count", len(items))
        set_attribute("cart_total", total)
        return total

    @trace
    async def charge_payment(user_id, amount):
        set_attribute("amount", amount)
        for attempt in range(1, MAX_ATTEMPTS + 1):
            set_attribute("attempts", attempt)
            try:
                return await call_gateway(user_id, amount)
            except GatewayError:
                if attempt == MAX_ATTEMPTS:
                    raise
                await asyncio.sleep(0.04)

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
        set_attribute("user_id", user_id)
        total = await validate_cart(items)
        txn = await charge_payment(user_id, total)
        await asyncio.gather(send_confirmation(user_id, txn), update_inventory(items))
        return txn

    return place_order
