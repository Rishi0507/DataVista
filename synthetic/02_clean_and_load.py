"""
RetailPulse — ETL: clean raw extracts and load into a SQLite warehouse.
This mirrors what an analyst does before any SQL/BI work: dedupe, fix nulls,
standardize categorical values, and validate business rules (no negative prices).
"""
import pandas as pd
import sqlite3

customers = pd.read_csv("raw_customers.csv")
orders = pd.read_csv("raw_orders.csv")

log = []

# --- Customers cleaning ---
before = len(customers)
customers = customers.drop_duplicates(subset="customer_id")
log.append(f"Customers: removed {before - len(customers)} duplicate rows")

before_null = customers["city"].isna().sum()
customers["city"] = customers["city"].fillna("Unknown")
log.append(f"Customers: filled {before_null} missing city values with 'Unknown'")

customers["gender"] = customers["gender"].str.upper().str[0].replace(
    {"O": "Other"}
).fillna("Other")

# campaign_assignment is the ground-truth treatment/control/not_eligible label per customer,
# needed for an unbiased (intent-to-treat) read of the campaign experiment.
assert "campaign_assignment" in customers.columns, "campaign_assignment column missing from raw extract"

# --- Orders cleaning ---
before = len(orders)
orders = orders.drop_duplicates(subset="order_id")
log.append(f"Orders: removed {before - len(orders)} duplicate rows")

bad_price = (orders["unit_price"] < 0).sum()
orders["unit_price"] = orders["unit_price"].abs()
orders["gross_amount"] = (orders["unit_price"] * orders["quantity"]).round(2)
orders["net_amount"] = (orders["gross_amount"] * (1 - orders["discount_pct"] / 100)).round(2)
log.append(f"Orders: corrected {bad_price} negative unit_price values (data entry sign error) and recalculated dependent amounts")

null_city = orders["city"].isna().sum()
orders["city"] = orders["city"].fillna("Unknown")
log.append(f"Orders: filled {null_city} missing city values with 'Unknown'")

orders["payment_method"] = orders["payment_method"].str.upper()
orders["order_date"] = pd.to_datetime(orders["order_date"])
customers["signup_date"] = pd.to_datetime(customers["signup_date"])

# Referential integrity: drop orders with no matching customer (shouldn't happen, but validate)
before = len(orders)
orders = orders[orders["customer_id"].isin(customers["customer_id"])]
log.append(f"Orders: dropped {before - len(orders)} orphaned rows with no matching customer")

# --- Load into SQLite ---
conn = sqlite3.connect("retailpulse.db")
customers.to_sql("customers", conn, if_exists="replace", index=False)
orders.to_sql("orders", conn, if_exists="replace", index=False)
conn.execute("CREATE INDEX idx_orders_customer ON orders(customer_id)")
conn.execute("CREATE INDEX idx_orders_date ON orders(order_date)")
conn.commit()
conn.close()

with open("cleaning_log.txt", "w") as f:
    f.write(f"Final row counts — customers: {len(customers):,} | orders: {len(orders):,}\n\n")
    f.write("\n".join(log))

print(f"Final: {len(customers):,} customers, {len(orders):,} orders loaded to retailpulse.db")
print("\n".join(log))
