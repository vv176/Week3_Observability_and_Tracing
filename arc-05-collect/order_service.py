"""Arc 5 - the program is unchanged. We now run it three times
so there is something to aggregate."""
import time

from tracer import trace, print_tree, slowest, total_by_name

INVENTORY = {"A19": 12, "B77": 3, "C45": 0}
PRICES = {"A19": 499.0, "B77": 1299.0, "C45": 89.0}


@trace
def check_inventory(sku, qty):
    time.sleep(0.03)
    return INVENTORY.get(sku, 0) >= qty


@trace
def validate_cart(items):
    total = 0.0
    for sku, qty in items:
        if not check_inventory(sku, qty):
            raise ValueError(f"{sku} is out of stock")
        total += PRICES[sku] * qty
    return total


@trace
def charge_payment(user_id, amount):
    time.sleep(0.20)
    return f"txn_{user_id}_{int(amount)}"


@trace
def send_confirmation(user_id, txn_id):
    time.sleep(0.07)
    return True


@trace
def place_order(user_id, items):
    total = validate_cart(items)
    txn = charge_payment(user_id, total)
    send_confirmation(user_id, txn)
    return txn


if __name__ == "__main__":
    place_order(4471, [("A19", 2), ("B77", 1)])
    print_tree()

    # Two more orders, so the aggregate questions have something to work on.
    
    place_order(4472, [("A19", 1)])
    place_order(4473, [("B77", 2), ("A19", 3)])

    slowest(3)
    total_by_name()
