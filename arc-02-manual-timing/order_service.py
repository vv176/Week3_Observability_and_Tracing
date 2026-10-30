"""Arc 2 - the simplest thing that works.

Timing is measured by hand inside every function.
Nothing is imported except the standard library.
"""
import time

INVENTORY = {"A19": 12, "B77": 3, "C45": 0}
PRICES = {"A19": 499.0, "B77": 1299.0, "C45": 89.0}


def check_inventory(sku, qty):
    t0 = time.perf_counter()
    result = INVENTORY.get(sku, 0) >= qty
    time.sleep(0.03)
    ms = (time.perf_counter() - t0) * 1000
    print(f"check_inventory    {ms:7.1f} ms  in={{'sku': {sku!r}, 'qty': {qty}}}  out={result}")
    return result


def validate_cart(items):
    t0 = time.perf_counter()
    total = 0.0
    for sku, qty in items:
        if not check_inventory(sku, qty):
            raise ValueError(f"{sku} is out of stock")
        total += PRICES[sku] * qty
    ms = (time.perf_counter() - t0) * 1000
    print(f"validate_cart      {ms:7.1f} ms  in={{'items': {items}}}  out={total}")
    return total


def charge_payment(user_id, amount):
    t0 = time.perf_counter()
    time.sleep(0.20)
    txn = f"txn_{user_id}_{int(amount)}"
    ms = (time.perf_counter() - t0) * 1000
    print(f"charge_payment     {ms:7.1f} ms  in={{'user_id': {user_id}, 'amount': {amount}}}  out={txn!r}")
    return txn


def send_confirmation(user_id, txn_id):
    t0 = time.perf_counter()
    time.sleep(0.07)
    ms = (time.perf_counter() - t0) * 1000
    print(f"send_confirmation  {ms:7.1f} ms  in={{'user_id': {user_id}, 'txn_id': {txn_id!r}}}  out=True")
    return True


def place_order(user_id, items):
    t0 = time.perf_counter()
    total = validate_cart(items)
    txn = charge_payment(user_id, total)
    send_confirmation(user_id, txn)
    ms = (time.perf_counter() - t0) * 1000
    print(f"place_order        {ms:7.1f} ms  in={{'user_id': {user_id}, 'items': {items}}}  out={txn!r}")
    return txn


if __name__ == "__main__":
    place_order(4471, [("A19", 2), ("B77", 1)])
