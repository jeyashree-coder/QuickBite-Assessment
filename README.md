# QuickBite Assessment

## What I understood

QuickBite has six related tables: orders, customers, restaurants, areas, delivery partners and feedback. The IDs connect these tables, so I treated `orders` as the main transaction table and used the other tables to add customer, restaurant, area, delivery-partner and feedback details.

The final combined file contains one row per cleaned order. The analysis uses only delivered orders, as requested. A delivery is considered late when `delivery_minutes > 45`.

## Problems found and how I fixed them

I found several data-quality issues in the source workbook:

- Duplicate records were present in multiple tables.
- Some duplicate order records differed only by capitalization or whitespace.
- Text fields had inconsistent capitalization, spelling and spacing.
- City values appeared in forms such as `BLR`, `Bengaluru`, `Hyd`, `Hyderabad`, `Madras`, `MUMBAI`, etc.
- Cuisine values included variants such as `Biriyani`/`Biryani`, `N. Indian`/`North Indian`/`North-Indian`, and `dessert`/`Desserts`.
- Vehicle values included variants such as `BIKE`, `Bike`, `Motorbike`, `Motor Bike`, `Cycle`, `Bicycle`, `Scooty`, `Scooter`, `e-scooter`, etc.
- Payment modes and order statuses had multiple case/wording variants.
- Dates were stored in several formats.
- Order amounts contained comma-formatted text.
- Delivery time contained values such as `15`, `15 min`, `15 mins`, and `16m`.
- Some optional fields were blank, such as coupon code, feedback comments, restaurant rating and customer email.
- Some orders had missing customer/restaurant/amount information, so those rows could not safely support a complete order record and were removed as missing mandatory data.

### Cleaning approach

1. Trim whitespace from text fields.
2. Standardize IDs to uppercase.
3. Standardize cities, cuisines, vehicle types, payment modes and order statuses.
4. Convert dates into real date/datetime values.
5. Convert order amounts into numeric values.
6. Convert delivery times into numeric minutes.
7. Remove exact duplicate rows after standardization.
8. Remove duplicate business keys so each table has one record per ID.
9. Remove rows missing fields defined as mandatory for that table.
10. Join the cleaned tables using their ID columns.
11. Calculate `order_date`, `order_time`, `order_day` and `is_late`.
12. Keep the final combined dataset at one row per order.

Optional blanks were retained rather than inventing values.

## How I calculated the analysis

### Area Performance

I used delivered orders only. For each area I calculated:

- Delivered orders
- Revenue = sum of `order_amount`
- Average order value
- Average delivery time
- Late orders
- Late rate = late delivered orders / delivered orders × 100
- Average customer rating

Areas are ranked from highest to lowest revenue.

### Top Cuisine by Day

For each day of the week, I counted delivered orders for every cuisine. The cuisine with the highest order count is shown as the top cuisine.

Share of the day's orders:

`cuisine orders / total delivered orders on that day × 100`

If two cuisines tie for first, both are retained.

### Vehicle Performance

For each vehicle type, I calculated:

- Delivered orders
- Revenue
- Average delivery time
- Late orders
- Late rate
- Average customer rating

The performance rank is based on the lowest late rate, so a lower late rate is better.

## How to run

From the `quickbite-assessment` folder:

```bash
python scripts/cleaning.py
python scripts/analysis.py
```

Run `cleaning.py` first because `analysis.py` uses the combined file created by it.

## Output files

- `cleaned_data/Quick_Bite_Data_Cleaning.xlsx` — cleaned source tables, one sheet per table.
- `cleaned_data/Quick_Bite_Combined_Data.xlsx` — one row per cleaned order with the required columns.
- `analysis/Quick_Bite_Analysis.xlsx` — Area Performance, Top Cuisine by Day and Vehicle Performance sheets.

## Important assumption

The assignment says to remove rows where mandatory data is blank but does not define every mandatory field. I treated the IDs needed to identify a record and the core order fields needed for analysis as mandatory. Optional descriptive fields were left blank when the source did not provide them.
