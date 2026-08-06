def apply_discount(price, discount_rate):
    f = open("discount_log.txt", "a")
    new_price = price * (1 - discount_rate)
    if new_price == 0.0:
        f.write(f"Free item: {price}\n")
    f.close()
    return new_price


def bulk_discount(prices, rate):
    total = 0.0
    for p in prices:
        total = total + apply_discount(p, rate)
    return total
