
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "QuickBite_Assessment.xlsx"
CLEANED = ROOT / "cleaned_data" / "Quick_Bite_Data_Cleaning.xlsx"
COMBINED = ROOT / "cleaned_data" / "Quick_Bite_Combined_Data.xlsx"

def clean_text(series):
    return series.apply(lambda x: np.nan if pd.isna(x) else str(x).strip())

def clean_id(series, upper=True):
    s = clean_text(series)
    return s.str.upper() if upper else s

def clean_date(series):
    return pd.to_datetime(clean_text(series), errors="coerce", dayfirst=True, format="mixed")

def clean_amount(series):
    s = clean_text(series).str.replace(",", "", regex=False)
    return pd.to_numeric(s, errors="coerce")

def clean_minutes(series):
    s = clean_text(series).str.lower()
    s = s.str.replace(r"[^0-9.]", "", regex=True)
    return pd.to_numeric(s, errors="coerce")

def standardize(df, name):
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = clean_text(df[col])

    if name == "areas":
        df["area_id"] = clean_id(df["area_id"])
        df["area_name"] = clean_text(df["area_name"]).str.title()
        city_map = {
            "blr": "Bengaluru", "bengaluru": "Bengaluru",
            "hyd": "Hyderabad", "hyderabad": "Hyderabad",
            "madras": "Chennai", "chennai": "Chennai",
            "mumbai": "Mumbai"
        }
        df["city"] = df["city"].str.lower().map(city_map)
        df["zone"] = df["zone"].str.title()

    elif name == "restaurants":
        df["restaurant_id"] = clean_id(df["restaurant_id"])
        df["restaurant_name"] = clean_text(df["restaurant_name"]).str.title()
        cuisine_map = {
            "biriyani": "Biryani", "biryani": "Biryani",
            "burgers": "Burgers", "chinese": "Chinese",
            "desserts": "Desserts", "dessert": "Desserts",
            "italian - pizza": "Pizza", "pizza": "Pizza",
            "n. indian": "North Indian", "north indian": "North Indian",
            "north-indian": "North Indian",
            "south indian": "South Indian", "south-indian": "South Indian"
        }
        df["cuisine"] = df["cuisine"].str.lower().map(cuisine_map)
        df["area_id"] = clean_id(df["area_id"])
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
        df["onboard_date"] = clean_date(df["onboard_date"])

    elif name == "delivery_partners":
        df["partner_id"] = clean_id(df["partner_id"])
        df["partner_name"] = clean_text(df["partner_name"]).str.title()
        vehicle_map = {
            "bike": "Bike", "motor bike": "Bike", "motorbike": "Bike",
            "bicycle": "Bicycle", "cycle": "Bicycle",
            "scooter": "Scooter", "scooty": "Scooter",
            "ev scooter": "EV Scooter", "e-scooter": "EV Scooter",
            "ev": "EV"
        }
        df["vehicle_type"] = df["vehicle_type"].str.lower().map(vehicle_map)
        df["join_date"] = clean_date(df["join_date"])

    elif name == "customers":
        df["customer_id"] = clean_id(df["customer_id"])
        df["customer_name"] = clean_text(df["customer_name"]).str.title()
        df["phone"] = clean_text(df["phone"]).str.replace(r"\s+", "", regex=True)
        df["area_id"] = clean_id(df["area_id"])
        df["signup_date"] = clean_date(df["signup_date"])
        # Email is optional in the source; blanks are retained as blanks.

    elif name == "orders":
        df["order_id"] = clean_id(df["order_id"])
        df["customer_id"] = clean_id(df["customer_id"])
        df["restaurant_id"] = clean_id(df["restaurant_id"])
        df["partner_id"] = clean_id(df["partner_id"])
        df["order_datetime"] = clean_date(df["order_datetime"])
        df["order_amount"] = clean_amount(df["order_amount"])
        payment_map = {
            "upi": "UPI", "gpay": "GPay", "phonepe": "PhonePe",
            "cash": "Cash", "cash on delivery": "Cash on Delivery", "cod": "Cash on Delivery",
            "card": "Card", "credit card": "Credit Card", "debit card": "Debit Card",
            "wallet": "Wallet", "paytm wallet": "Paytm Wallet", "amazon pay": "Amazon Pay"
        }
        df["payment_mode"] = df["payment_mode"].str.lower().map(payment_map)
        status_map = {
            "delivered": "Delivered", "completed": "Delivered",
            "cancelled": "Cancelled", "canceled": "Cancelled"
        }
        df["order_status"] = df["order_status"].str.lower().map(status_map)
        df["delivery_minutes"] = clean_minutes(df["delivery_minutes"])
        df["coupon_code"] = clean_text(df["coupon_code"]).str.upper()

    elif name == "feedback":
        df["feedback_id"] = clean_id(df["feedback_id"])
        df["order_id"] = clean_id(df["order_id"])
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
        df["comment"] = clean_text(df["comment"])
        df["feedback_date"] = clean_date(df["feedback_date"])

    # Remove exact duplicate records after standardization.
    df = df.drop_duplicates().reset_index(drop=True)
    return df

def main():
    sheets = pd.read_excel(INPUT, sheet_name=None)
    cleaned = {name: standardize(df, name) for name, df in sheets.items()}

    # Mandatory fields for each table. Optional fields such as restaurant rating,
    # customer email/area, feedback rating/comment, coupon code and delivery time
    # are retained when missing.
    mandatory = {
        "areas": ["area_id", "area_name", "city", "zone"],
        "restaurants": ["restaurant_id", "restaurant_name", "area_id", "cuisine", "onboard_date"],
        "delivery_partners": ["partner_id", "partner_name", "vehicle_type", "join_date"],
        "customers": ["customer_id", "customer_name", "phone", "signup_date"],
        "orders": ["order_id", "customer_id", "restaurant_id", "order_datetime",
                   "order_amount", "payment_mode", "order_status"],
        "feedback": ["feedback_id", "order_id", "feedback_date"]
    }

    for name, cols in mandatory.items():
        cleaned[name] = cleaned[name].dropna(subset=cols).reset_index(drop=True)

    # Enforce one record per business key after standardization.
    # This removes duplicate source records whose only difference was formatting/case.
    key_columns = {
        "areas": "area_id",
        "restaurants": "restaurant_id",
        "delivery_partners": "partner_id",
        "customers": "customer_id",
        "orders": "order_id",
        "feedback": "feedback_id"
    }
    for name, key in key_columns.items():
        cleaned[name] = cleaned[name].drop_duplicates(subset=[key], keep="first").reset_index(drop=True)

    with pd.ExcelWriter(CLEANED, engine="openpyxl") as writer:
        for name, df in cleaned.items():
            df.to_excel(writer, sheet_name=name, index=False)

    # Build one row per order. LEFT joins preserve the cleaned order table.
    orders = cleaned["orders"].copy()
    orders["order_date"] = orders["order_datetime"].dt.date
    orders["order_time"] = orders["order_datetime"].dt.strftime("%H:%M:%S")
    orders["order_day"] = orders["order_datetime"].dt.day_name()
    orders["is_late"] = np.where(
        orders["delivery_minutes"].notna(),
        orders["delivery_minutes"] > 45,
        np.nan
    )

    combined = (
        orders.merge(cleaned["customers"][["customer_id", "customer_name"]],
                     on="customer_id", how="left")
              .merge(cleaned["restaurants"][["restaurant_id", "restaurant_name", "area_id", "cuisine"]],
                     on="restaurant_id", how="left")
              .merge(cleaned["areas"][["area_id", "area_name", "city"]],
                     on="area_id", how="left")
              .merge(cleaned["delivery_partners"][["partner_id", "partner_name", "vehicle_type"]],
                     on="partner_id", how="left")
              .merge(cleaned["feedback"][["order_id", "rating", "comment"]],
                     on="order_id", how="left")
    )

    columns = [
        "order_id", "order_date", "order_time", "order_day",
        "customer_name", "restaurant_name", "cuisine", "area_name", "city",
        "partner_name", "vehicle_type", "order_amount", "payment_mode",
        "coupon_code", "order_status", "delivery_minutes", "is_late",
        "rating", "comment"
    ]
    combined = combined[columns].drop_duplicates(subset=["order_id"]).reset_index(drop=True)

    with pd.ExcelWriter(COMBINED, engine="openpyxl") as writer:
        combined.to_excel(writer, sheet_name="combined_data", index=False)

    print(f"Created: {CLEANED}")
    print(f"Created: {COMBINED}")
    print(f"Cleaned order rows: {len(orders)}")
    print(f"Combined rows: {len(combined)}")

if __name__ == "__main__":
    main()
