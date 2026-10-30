"""The program we will trace for the rest of the class.

There is no tracing here. This is an ordinary Python program.
"""
import time

INVENTORY = {"A19": 12, "B77": 3, "C45": 0}
PRICES = {"A19": 499.0, "B77": 1299.0, "C45": 89.0}


def check_inventory(sku, qty):
    time.sleep(0.03)                      # stands in for a database query
    return INVENTORY.get(sku, 0) >= qty


def validate_cart(items):
    total = 0.0
    for sku, qty in items:
        if not check_inventory(sku, qty):
            raise ValueError(f"{sku} is out of stock")
        total += PRICES[sku] * qty
    return total


def charge_payment(user_id, amount):
    time.sleep(0.20)                      # stands in for the payment gateway
    return f"txn_{user_id}_{int(amount)}"


def send_confirmation(user_id, txn_id):
    time.sleep(0.07)                      # stands in for the email service
    return True


def place_order(user_id, items):
    total = validate_cart(items)
    txn = charge_payment(user_id, total)
    send_confirmation(user_id, txn)
    return txn


if __name__ == "__main__":
    result = place_order(4471, [("A19", 2), ("B77", 1)])
    print(f"Order confirmed: {result}")
