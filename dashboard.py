from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd
import plotly.express as px
import streamlit as st


STATUS_COLORS = {
    "FULFILLED": "#2E7D32",  # green
    "PARTIAL": "#F9A825",  # yellow
    "REJECTED": "#C62828",  # red
}


@st.cache_data(ttl=10)
def load_data(base_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    root = Path(base_dir)
    fulfillment = pd.read_csv(root / "fulfillment_report.csv")
    stock = pd.read_csv(root / "stock_remaining.csv")
    products = pd.read_csv(root / "products.csv")
    return fulfillment, stock, products


def build_stock_insights(stock_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
    merged = products_df.rename(columns={"available_stock": "initial_stock"})[
        ["product_id", "product_name", "initial_stock"]
    ].merge(stock_df, on="product_id", how="left")
    merged["remaining_stock"] = merged["remaining_stock"].fillna(0).astype(int)
    merged["initial_stock"] = merged["initial_stock"].fillna(0).astype(int)
    return merged.sort_values("product_id").reset_index(drop=True)


def kpi_card(title: str, value: int, color: str, icon: str) -> None:
    st.markdown(
        f"""
        <div style="
            border-radius: 14px;
            padding: 16px 18px;
            border: 1px solid #e6e6e6;
            background: linear-gradient(135deg, #ffffff 0%, #f9f9f9 100%);
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        ">
            <div style="font-size: 13px; color: #666;">{icon} {title}</div>
            <div style="font-size: 28px; font-weight: 700; color: {color};">{value:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def main() -> None:
    st.set_page_config(
        page_title="Warehouse Fulfillment Dashboard",
        page_icon="📦",
        layout="wide",
    )
    st.title("📦 Warehouse Order Fulfillment & Stock Dashboard")
    st.caption("Interactive analytics for order outcomes and inventory health")

    root_dir = Path(__file__).resolve().parent
    fulfillment_df, stock_df, products_df = load_data(str(root_dir))

    fulfillment_df["order_date_parsed"] = pd.to_datetime(
        fulfillment_df["order_date"], errors="coerce"
    )
    stock_insights_df = build_stock_insights(stock_df, products_df)

    st.sidebar.header("Filters & Controls")
    low_stock_threshold = st.sidebar.slider("Low stock threshold", min_value=1, max_value=100, value=10)
    if st.sidebar.button("Refresh data"):
        st.cache_data.clear()
        st.rerun()

    status_options = sorted(fulfillment_df["status"].dropna().unique().tolist())
    selected_statuses = st.sidebar.multiselect(
        "Order status",
        options=status_options,
        default=status_options,
    )

    product_options = sorted(fulfillment_df["product_id"].dropna().unique().tolist())
    selected_products = st.sidebar.multiselect(
        "Product",
        options=product_options,
        default=product_options,
    )

    min_date = fulfillment_df["order_date_parsed"].min()
    max_date = fulfillment_df["order_date_parsed"].max()
    if pd.notna(min_date) and pd.notna(max_date):
        selected_range = st.sidebar.date_input(
            "Date range",
            value=(min_date.date(), max_date.date()),
        )
    else:
        selected_range = ()

    search_text = st.sidebar.text_input("Search order ID / product / reason", "")

    filtered_orders = fulfillment_df[
        fulfillment_df["status"].isin(selected_statuses)
        & fulfillment_df["product_id"].isin(selected_products)
    ].copy()

    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start, end = pd.to_datetime(selected_range[0]), pd.to_datetime(selected_range[1])
        filtered_orders = filtered_orders[
            filtered_orders["order_date_parsed"].between(start, end, inclusive="both")
        ]

    if search_text.strip():
        needle = search_text.strip().lower()
        search_cols = ["order_id", "product_id", "reason"]
        mask = pd.Series(False, index=filtered_orders.index)
        for col in search_cols:
            mask = mask | filtered_orders[col].fillna("").astype(str).str.lower().str.contains(needle)
        filtered_orders = filtered_orders[mask]

    fulfilled_count = int((filtered_orders["status"] == "FULFILLED").sum())
    partial_count = int((filtered_orders["status"] == "PARTIAL").sum())
    rejected_count = int((filtered_orders["status"] == "REJECTED").sum())
    total_orders = int(len(filtered_orders))
    total_remaining_stock = int(stock_insights_df["remaining_stock"].sum())

    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        kpi_card("Total Orders Processed", total_orders, "#1E88E5", "📊")
    with kpi_cols[1]:
        kpi_card("Total Fulfilled Orders", fulfilled_count, STATUS_COLORS["FULFILLED"], "✅")
    with kpi_cols[2]:
        kpi_card("Partial Fulfillments", partial_count, STATUS_COLORS["PARTIAL"], "⚠️")
    with kpi_cols[3]:
        kpi_card("Rejected Orders", rejected_count, STATUS_COLORS["REJECTED"], "❌")
    with kpi_cols[4]:
        kpi_card("Total Remaining Stock", total_remaining_stock, "#6A1B9A", "📦")

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)
    status_counts = (
        filtered_orders["status"]
        .value_counts()
        .reindex(["FULFILLED", "PARTIAL", "REJECTED"], fill_value=0)
        .reset_index()
    )
    status_counts.columns = ["status", "count"]

    with chart_col1:
        st.subheader("Order Fulfillment Overview (Bar)")
        bar_fig = px.bar(
            status_counts,
            x="status",
            y="count",
            color="status",
            color_discrete_map=STATUS_COLORS,
            text="count",
        )
        bar_fig.update_layout(showlegend=False, height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(bar_fig, use_container_width=True)

    with chart_col2:
        st.subheader("Fulfillment Distribution (Pie)")
        pie_fig = px.pie(
            status_counts,
            names="status",
            values="count",
            color="status",
            color_discrete_map=STATUS_COLORS,
            hole=0.45,
        )
        pie_fig.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(pie_fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Stock Insights")
    low_stock_df = stock_insights_df[stock_insights_df["remaining_stock"] < low_stock_threshold].copy()

    if not low_stock_df.empty:
        st.error(f"Low-stock alert: {len(low_stock_df)} product(s) below threshold {low_stock_threshold}.")
    else:
        st.success("No products currently below low-stock threshold.")

    display_stock = stock_insights_df.rename(
        columns={
            "product_id": "Product ID",
            "product_name": "Product Name",
            "initial_stock": "Initial Stock",
            "remaining_stock": "Remaining Stock",
        }
    )
    st.dataframe(
        display_stock.style.apply(
            lambda row: [
                "background-color: #ffebee; color: #b71c1c;"
                if row["Remaining Stock"] < low_stock_threshold
                else ""
                for _ in row
            ],
            axis=1,
        ),
        use_container_width=True,
        hide_index=True,
    )

    stock_search = st.text_input("Search stock by Product ID or Name", "")
    stock_filtered = display_stock.copy()
    if stock_search.strip():
        s = stock_search.strip().lower()
        stock_filtered = stock_filtered[
            stock_filtered["Product ID"].str.lower().str.contains(s)
            | stock_filtered["Product Name"].str.lower().str.contains(s)
        ]

    st.download_button(
        "Download Stock Table (CSV)",
        data=to_csv_bytes(stock_filtered),
        file_name="stock_remaining_filtered.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.subheader("Order Details")
    order_display = filtered_orders.drop(columns=["order_date_parsed"]).rename(
        columns={
            "order_id": "Order ID",
            "product_id": "Product ID",
            "request_quantity": "Requested Qty",
            "fulfilled_quantity": "Fulfilled Qty",
            "status": "Status",
            "order_date": "Order Date",
            "reason": "Reason",
        }
    )
    st.dataframe(order_display, use_container_width=True, hide_index=True)

    st.download_button(
        "Download Filtered Orders (CSV)",
        data=to_csv_bytes(order_display),
        file_name="fulfillment_report_filtered.csv",
        mime="text/csv",
    )

    st.info(
        "Layout preview: Top KPI cards, center charts (bar + pie), "
        "then stock insights with low-stock highlights, and order details at the bottom."
    )


if __name__ == "__main__":
    main()
