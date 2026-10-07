from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Item:
    sku: str
    price: Decimal
    qty: int


@dataclass
class Order:
    order_id: str
    items: list = field(default_factory=list)
    discount_pct: Decimal = Decimal("0")
    status: str = "open"

    def subtotal(self) -> Decimal:
        return sum((i.price * i.qty for i in self.items), Decimal("0"))

    def total(self) -> Decimal:
        discount = self.subtotal() * self.discount_pct / 100
        return (self.subtotal() - discount).quantize(Decimal("0.01"))


class Inventory:
    def __init__(self, stock: dict):
        self.stock = dict(stock)

    def available(self, sku: str) -> int:
        return self.stock.get(sku, 0)

    def reserve(self, order: Order) -> bool:
        """Reserve every item of the order, or nothing at all."""
        for item in order.items:
            if self.available(item.sku) < item.qty:
                return False
            self.stock[item.sku] -= item.qty
        return True

    def release(self, order: Order) -> None:
        for item in order.items:
            self.stock[item.sku] = item.qty


def place_order(order: Order, inventory: Inventory) -> str:
    if order.status != "open":
        raise ValueError(f"order {order.order_id} is {order.status}")
    if not order.items:
        raise ValueError("empty order")
    if order.discount_pct < 0 or order.discount_pct > 100:
        raise ValueError("discount out of range")
    if not inventory.reserve(order):
        order.status = "rejected"
        return order.status
    order.status = "placed"
    return order.status


def cancel_order(order: Order, inventory: Inventory) -> None:
    if order.status == "placed":
        inventory.release(order)
    order.status = "cancelled"
