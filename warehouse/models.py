from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Order:
    order_id: str
    product_id: str
    quantity: int
    order_date: str  


@dataclass(frozen=True, slots=True)
class OrderResult:
    order_id: str
    product_id: str
    request_quantity: int
    fulfilled_quantity: int
    status: str  # FULFILLED | PARTIAL | REJECTED
    order_date: str
    reason: str = ""

