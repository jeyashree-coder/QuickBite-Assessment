
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "cleaned_data" / "Quick_Bite_Combined_Data.xlsx"
OUTPUT = ROOT / "analysis" / "Quick_Bite_Analysis.xlsx"

def main():
    df = pd.read_excel(INPUT, sheet_name="combined_data")
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["order_amount"] = pd.to_numeric(df["order_amount"], errors="coerce")
    df["delivery_minutes"] = pd.to_numeric(df["delivery_minutes"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    delivered = df[df["order_status"].eq("Delivered")].copy()
    delivered["is_late"] = delivered["delivery_minutes"].gt(45)

    # 1. Area Performance
    area = delivered.groupby(["area_name", "city"], dropna=False).agg(
        delivered_orders=("order_id", "count"),
        revenue=("order_amount", "sum"),
        avg_order_value=("order_amount", "mean"),
        avg_delivery_minutes=("delivery_minutes", "mean"),
        late_orders=("is_late", "sum"),
        avg_rating=("rating", "mean")
    ).reset_index()
    area["late_rate_pct"] = np.where(
        area["delivered_orders"].gt(0),
        area["late_orders"] / area["delivered_orders"] * 100,
        np.nan
    )
    area["revenue_rank"] = area["revenue"].rank(method="dense", ascending=False).astype(int)
    area = area.sort_values(["revenue_rank", "area_name"])
    area = area[
        ["revenue_rank", "area_name", "city", "delivered_orders", "revenue",
         "avg_order_value", "avg_delivery_minutes", "late_orders",
         "late_rate_pct", "avg_rating"]
    ]

    # 2. Top Cuisine by Day
    cuisine_counts = (
        delivered.groupby(["order_day", "cuisine"], dropna=False)
        .size().reset_index(name="orders")
    )
    day_totals = delivered.groupby("order_day").size().reset_index(name="day_total_orders")
    cuisine_counts = cuisine_counts.merge(day_totals, on="order_day", how="left")
    cuisine_counts["share_pct"] = cuisine_counts["orders"] / cuisine_counts["day_total_orders"] * 100
    cuisine_counts["rank"] = cuisine_counts.groupby("order_day")["orders"].rank(
        method="dense", ascending=False
    )
    top_cuisine = cuisine_counts[cuisine_counts["rank"].eq(1)].copy()
    top_cuisine = top_cuisine.sort_values(
        by=["order_day", "orders", "cuisine"], ascending=[True, False, True]
    )
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    top_cuisine["order_day"] = pd.Categorical(
        top_cuisine["order_day"], categories=weekday_order, ordered=True
    )
    top_cuisine = top_cuisine.sort_values("order_day")
    top_cuisine = top_cuisine[
        ["order_day", "cuisine", "orders", "day_total_orders", "share_pct"]
    ]

    # 3. Vehicle Performance
    vehicle = delivered.groupby("vehicle_type", dropna=False).agg(
        delivered_orders=("order_id", "count"),
        revenue=("order_amount", "sum"),
        avg_delivery_minutes=("delivery_minutes", "mean"),
        late_orders=("is_late", "sum"),
        avg_rating=("rating", "mean")
    ).reset_index()
    vehicle["late_rate_pct"] = np.where(
        vehicle["delivered_orders"].gt(0),
        vehicle["late_orders"] / vehicle["delivered_orders"] * 100,
        np.nan
    )
    vehicle["performance_rank"] = vehicle["late_rate_pct"].rank(
        method="dense", ascending=True
    ).astype(int)
    vehicle = vehicle.sort_values(["performance_rank", "vehicle_type"])
    vehicle = vehicle[
        ["performance_rank", "vehicle_type", "delivered_orders", "revenue",
         "avg_delivery_minutes", "late_orders", "late_rate_pct", "avg_rating"]
    ]

    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        area.to_excel(writer, sheet_name="Area Performance", index=False)
        top_cuisine.to_excel(writer, sheet_name="Top Cuisine by Day", index=False)
        vehicle.to_excel(writer, sheet_name="Vehicle Performance", index=False)

    print(f"Created: {OUTPUT}")

if __name__ == "__main__":
    main()
