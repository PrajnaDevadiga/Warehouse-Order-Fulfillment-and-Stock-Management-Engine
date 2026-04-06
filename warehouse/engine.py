from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .models import Order, OrderResult


STATUS_FULFILLED = "FULFILLED"
STATUS_PARTIAL = "PARTIAL"
STATUS_REJECTED = "REJECTED"


def _parse_date_yyyy_mm_dd(value: str) -> datetime.date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception as e:  # noqa: BLE001 - we want a consistent rejection reason
        raise ValueError(f"Invalid date: {value!r}") from e


@dataclass
class WarehouseEngine:
    _inventory: dict[str, int]

    def __init__(self, inventory: dict[str, int]):
        # Copy to avoid mutating caller input.
        self._inventory = {pid: int(stock) for pid, stock in inventory.items()}

    def get_stock_remaining(self) -> dict[str, int]:
        return dict(self._inventory)

    def process_order(self, order: Order) -> OrderResult:
        # 1) Validate
        product_stock = self._inventory.get(order.product_id)
        if product_stock is None:
            return OrderResult(
                order_id=order.order_id,
                product_id=order.product_id,
                request_quantity=order.quantity,
                fulfilled_quantity=0,
                status=STATUS_REJECTED,
                order_date=order.order_date,
                reason="Invalid product",
            )

        if order.quantity <= 0:
            return OrderResult(
                order_id=order.order_id,
                product_id=order.product_id,
                request_quantity=order.quantity,
                fulfilled_quantity=0,
                status=STATUS_REJECTED,
                order_date=order.order_date,
                reason="Quantity must be > 0",
            )

        try:
            _parse_date_yyyy_mm_dd(order.order_date)
        except ValueError:
            return OrderResult(
                order_id=order.order_id,
                product_id=order.product_id,
                request_quantity=order.quantity,
                fulfilled_quantity=0,
                status=STATUS_REJECTED,
                order_date=order.order_date,
                reason="Invalid order date",
            )

        # 2) Fulfill / Partial
        if order.quantity <= product_stock:
            self._inventory[order.product_id] = product_stock - order.quantity
            return OrderResult(
                order_id=order.order_id,
                product_id=order.product_id,
                request_quantity=order.quantity,
                fulfilled_quantity=order.quantity,
                status=STATUS_FULFILLED,
                order_date=order.order_date,
                reason="",
            )

        # order.quantity > product_stock
        if product_stock > 0:
            fulfilled = product_stock
            self._inventory[order.product_id] = 0
            return OrderResult(
                order_id=order.order_id,
                product_id=order.product_id,
                request_quantity=order.quantity,
                fulfilled_quantity=fulfilled,
                status=STATUS_PARTIAL,
                order_date=order.order_date,
                reason="Insufficient stock (partial fulfillment)",
            )

        # stock == 0, nothing to fulfill
        self._inventory[order.product_id] = 0
        return OrderResult(
            order_id=order.order_id,
            product_id=order.product_id,
            request_quantity=order.quantity,
            fulfilled_quantity=0,
            status=STATUS_REJECTED,
            order_date=order.order_date,
            reason="Insufficient stock",
        )

    def process_orders(self, orders: Iterable[Order]) -> tuple[list[OrderResult], dict[str, int]]:
        results: list[OrderResult] = []
        for order in orders:
            results.append(self.process_order(order))
        return results, self.get_stock_remaining()

