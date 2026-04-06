from __future__ import annotations

import csv
from pathlib import Path

from .engine import WarehouseEngine
from .models import Order


def load_inventory(products_csv_path: str | Path) -> dict[str, int]:
    products_csv_path = Path(products_csv_path)
    inventory: dict[str, int] = {}

    with products_csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            product_id = (row.get("product_id") or "").strip()
            available_stock_raw = row.get("available_stock")
            if not product_id:
                continue
            try:
                available_stock = int(available_stock_raw)
            except Exception:
                available_stock = 0
            if available_stock < 0:
                available_stock = 0
            inventory[product_id] = available_stock

    return inventory


def load_orders(orders_csv_path: str | Path) -> list[Order]:
    orders_csv_path = Path(orders_csv_path)
    orders: list[Order] = []

    with orders_csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            order_id = (row.get("order_id") or "").strip()
            product_id = (row.get("product_id") or "").strip()
            quantity_raw = row.get("quantity")
            order_date = (row.get("order_date") or "").strip()

            try:
                quantity = int(quantity_raw)
            except Exception:
                # Invalid quantity format -> tests for validation use engine directly;
                # here we coerce to 0 so it becomes a rejection later.
                quantity = 0

            if order_id and product_id:
                orders.append(
                    Order(
                        order_id=order_id,
                        product_id=product_id,
                        quantity=quantity,
                        order_date=order_date,
                    )
                )

    return orders


def write_fulfillment_report(
    fulfillment_report_csv_path: str | Path, results: list
) -> None:
    fulfillment_report_csv_path = Path(fulfillment_report_csv_path)
    with fulfillment_report_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "order_id",
                "product_id",
                "request_quantity",
                "fulfilled_quantity",
                "status",
                "order_date",
                "reason",
            ],
        )
        writer.writeheader()

        for r in results:
            writer.writerow(
                {
                    "order_id": r.order_id,
                    "product_id": r.product_id,
                    "request_quantity": r.request_quantity,
                    "fulfilled_quantity": r.fulfilled_quantity,
                    "status": r.status,
                    "order_date": r.order_date,
                    "reason": r.reason,
                }
            )


def write_stock_remaining(stock_remaining_csv_path: str | Path, inventory: dict[str, int]) -> None:
    stock_remaining_csv_path = Path(stock_remaining_csv_path)
    with stock_remaining_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["product_id", "remaining_stock"])
        writer.writeheader()
        for product_id in sorted(inventory.keys()):
            writer.writerow({"product_id": product_id, "remaining_stock": inventory[product_id]})


def run_fulfillment(
    products_csv_path: str | Path,
    orders_csv_path: str | Path,
    fulfillment_report_csv_path: str | Path,
    stock_remaining_csv_path: str | Path,
) -> None:
    inventory = load_inventory(products_csv_path)
    orders = load_orders(orders_csv_path)
    engine = WarehouseEngine(inventory)
    results, remaining = engine.process_orders(orders)
    write_fulfillment_report(fulfillment_report_csv_path, results)
    write_stock_remaining(stock_remaining_csv_path, remaining)

