import pandas as pd
import sqlite3

RAW_DIR = "raw"
STUDY_START = pd.Timestamp("2016-01-01")  

log = []

# customers
transactions = pd.read_csv(f"{RAW_DIR}/transaction_data.csv")
hh_demo = pd.read_csv(f"{RAW_DIR}/hh_demographic.csv")

all_households = pd.DataFrame({"household_key": transactions["household_key"].unique()})
customers = all_households.merge(hh_demo, on="household_key", how="left")

demo_cols = ["AGE_DESC", "MARITAL_STATUS_CODE", "INCOME_DESC", "HOMEOWNER_DESC",
             "HH_COMP_DESC", "HOUSEHOLD_SIZE_DESC", "KID_CATEGORY_DESC"]
missing_before = customers[demo_cols].isna().all(axis=1).sum()
customers[demo_cols] = customers[demo_cols].fillna("Unknown")
log.append(f"Customers: {missing_before} of {len(customers)} households have NO demographic record (real gap in source data, filled 'Unknown')")

# order-level baskets
transactions["order_date"] = STUDY_START + pd.to_timedelta(transactions["DAY"], unit="D")

baskets = transactions.groupby(["household_key", "BASKET_ID"]).agg(
    order_date=("order_date", "first"),
    store_id=("STORE_ID", "first"),
    n_items=("PRODUCT_ID", "count"),
    total_quantity=("QUANTITY", "sum"),
    gross_sales_value=("SALES_VALUE", "sum"),
    retail_discount=("RETAIL_DISC", "sum"),   
    coupon_discount=("COUPON_DISC", "sum"),
    coupon_match_discount=("COUPON_MATCH_DISC", "sum"),
).reset_index()
log.append(f"Baskets: {len(baskets):,} distinct shopping trips built from {len(transactions):,} line items")

# basket items
product = pd.read_csv(f"{RAW_DIR}/product.csv")
basket_items = transactions.merge(product, on="PRODUCT_ID", how="left")
basket_items["DEPARTMENT"] = basket_items["DEPARTMENT"].fillna("Unknown")
missing_product = basket_items["DEPARTMENT"].eq("Unknown").sum()
log.append(f"Basket items: {missing_product} of {len(basket_items):,} line items have no matching product record")

basket_items = basket_items[["household_key", "BASKET_ID", "PRODUCT_ID", "order_date",
                               "QUANTITY", "SALES_VALUE", "RETAIL_DISC",
                               "DEPARTMENT", "COMMODITY_DESC", "SUB_COMMODITY_DESC", "BRAND"]]

# load to sqlite
conn = sqlite3.connect("retailpulse_real.db")
customers.to_sql("customers", conn, if_exists="replace", index=False)
baskets.to_sql("baskets", conn, if_exists="replace", index=False)
basket_items.to_sql("basket_items", conn, if_exists="replace", index=False)
conn.execute("CREATE INDEX idx_baskets_hh ON baskets(household_key)")
conn.execute("CREATE INDEX idx_baskets_date ON baskets(order_date)")
conn.execute("CREATE INDEX idx_items_basket ON basket_items(BASKET_ID)")
conn.commit()
conn.close()

with open("cleaning_log.txt", "w") as f:
    f.write(f"Final: {len(customers):,} customers | {len(baskets):,} baskets | {len(basket_items):,} basket items\n\n")
    f.write("\n".join(log))

print(f"Loaded: {len(customers):,} customers, {len(baskets):,} baskets, {len(basket_items):,} basket items")
print("\n".join(log))