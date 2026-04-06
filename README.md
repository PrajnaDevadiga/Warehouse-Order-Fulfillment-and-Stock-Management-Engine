# Warehouse Order Fulfillment & Stock Management Engine (Python)

This project processes product inventory and customer orders from CSV files, validates each order, updates stock, and generates:

- `fulfillment_report.csv`
- `stock_remaining.csv`

## Input files

The app expects these CSVs in the project root:

- `products.csv` (inventory)
  - Columns: `product_id, product_name, available_stock, price`
- `warehouse_orders.csv` (orders)
  - Columns: `order_id, product_id, quantity, order_date`

## Fulfillment rules

- `product` must exist in `products.csv`
- `quantity` must be `> 0`
- `order_date` must be a valid date in `YYYY-MM-DD` format
- If `quantity <= stock` → `FULFILLED` (deduct stock)
- If `quantity > stock` → `PARTIAL` (fulfill what’s available and set stock to `0`)
  - If stock is already `0`, the order is marked `REJECTED`

## Outputs

- `fulfillment_report.csv`
  - `order_id, product_id, request_quantity, fulfilled_quantity, status, order_date, reason`
- `stock_remaining.csv`
  - `product_id, remaining_stock`

## Run the application

1. Install dependencies:
   - `python -m pip install -r requirements.txt`
2. Run:
   - `python run_fulfillment.py`

Optional arguments:
- `--products products.csv`
- `--orders warehouse_orders.csv`
- `--output-dir .`

## Run unit tests

- `pytest -q`

