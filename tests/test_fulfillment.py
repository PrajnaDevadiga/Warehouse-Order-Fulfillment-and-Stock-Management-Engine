import pytest

from warehouse.engine import WarehouseEngine, STATUS_FULFILLED, STATUS_PARTIAL, STATUS_REJECTED
from warehouse.models import Order


def test_invalid_product_rejected():
    engine = WarehouseEngine({"P001": 10})
    order = Order(order_id="O1", product_id="P999", quantity=2, order_date="2024-08-01")
    result = engine.process_order(order)

    assert result.status == STATUS_REJECTED
    assert "product" in result.reason.lower()


def test_negative_quantity_rejected():
    engine = WarehouseEngine({"P001": 10})
    order = Order(order_id="O1", product_id="P001", quantity=-1, order_date="2024-08-01")
    result = engine.process_order(order)

    assert result.status == STATUS_REJECTED
    assert "quant" in result.reason.lower()


def test_stock_deduction():
    engine = WarehouseEngine({"P001": 10})
    order = Order(order_id="O1", product_id="P001", quantity=10, order_date="2024-08-01")
    engine.process_order(order)

    assert engine.get_stock_remaining()["P001"] == 0


def test_partial_fulfillment():
    engine = WarehouseEngine({"P001": 10})
    order = Order(order_id="O1", product_id="P001", quantity=15, order_date="2024-08-01")
    result = engine.process_order(order)

    assert result.status == STATUS_PARTIAL
    assert result.fulfilled_quantity == 10
    assert engine.get_stock_remaining()["P001"] == 0


def test_full_fulfillment():
    engine = WarehouseEngine({"P001": 10})
    order = Order(order_id="O1", product_id="P001", quantity=10, order_date="2024-08-01")
    result = engine.process_order(order)

    assert result.status == STATUS_FULFILLED
    assert result.fulfilled_quantity == 10
    assert engine.get_stock_remaining()["P001"] == 0

