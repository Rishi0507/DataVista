import pandas as pd

RAW_DIR = "raw"

transactions = pd.read_csv(f"{RAW_DIR}/transaction_data.csv")
hh_demo = pd.read_csv(f"{RAW_DIR}/hh_demographic.csv")
product = pd.read_csv(f"{RAW_DIR}/product.csv")
campaign_table = pd.read_csv(f"{RAW_DIR}/campaign_table.csv")
campaign_desc = pd.read_csv(f"{RAW_DIR}/campaign_desc.csv")
coupon = pd.read_csv(f"{RAW_DIR}/coupon.csv")
coupon_redempt = pd.read_csv(f"{RAW_DIR}/coupon_redempt.csv")

print("=== Row counts ===")
print("transactions:", len(transactions))
print("hh_demographic:", len(hh_demo))
print("product:", len(product))
print("campaign_table:", len(campaign_table))
print("campaign_desc:", len(campaign_desc))
print("coupon:", len(coupon))
print("coupon_redempt:", len(coupon_redempt))

print("\n=== Columns ===")
for name, df in [("transactions", transactions), ("hh_demographic", hh_demo),
                  ("product", product), ("campaign_table", campaign_table),
                  ("campaign_desc", campaign_desc), ("coupon", coupon),
                  ("coupon_redempt", coupon_redempt)]:
    print(f"{name}: {df.columns.tolist()}")

print("\n=== Key overlaps ===")
print("Unique households in transactions:", transactions["household_key"].nunique())
print("Households with demographics:", hh_demo["household_key"].nunique())
print("Households that received a campaign:", campaign_table["household_key"].nunique())

print("\n=== Nulls (top 10 columns by null count, transactions) ===")
print(transactions.isna().sum().sort_values(ascending=False).head(10))

print("\n=== Sample rows ===")
print(transactions.head(3))