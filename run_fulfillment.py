from __future__ import annotations

import argparse
from pathlib import Path

from warehouse.io import run_fulfillment


def main() -> None:
    parser = argparse.ArgumentParser(description="Warehouse fulfillment & stock management engine")
    parser.add_argument("--products", default="products.csv", help="Path to products.csv")
    parser.add_argument("--orders", default="warehouse_orders.csv", help="Path to warehouse_orders.csv")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory where fulfillment_report.csv and stock_remaining.csv will be written",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_fulfillment(
        products_csv_path=args.products,
        orders_csv_path=args.orders,
        fulfillment_report_csv_path=output_dir / "fulfillment_report.csv",
        stock_remaining_csv_path=output_dir / "stock_remaining.csv",
    )


if __name__ == "__main__":
    main()

