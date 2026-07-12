import numpy as np
import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)
fake = Faker("en_IN")
Faker.seed(42)

N_CUSTOMERS = 6000
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31)

REGIONS = {
    "Mumbai": "Tier 1", "Delhi": "Tier 1", "Bengaluru": "Tier 1", "Pune": "Tier 1",
    "Ahmedabad": "Tier 1", "Jaipur": "Tier 2", "Lucknow": "Tier 2", "Indore": "Tier 2",
    "Nagpur": "Tier 2", "Bhopal": "Tier 2", "Ranchi": "Tier 3", "Kota": "Tier 3", "Guwahati": "Tier 3"
}
CHANNELS = ["Organic Search", "Paid Social", "Referral", "Email", "Direct"]
CHANNEL_WEIGHTS = [0.32, 0.27, 0.13, 0.13, 0.15]

CATEGORIES = {
    "Mobiles & Accessories": (800, 45000),
    "Home Appliances": (1200, 38000),
    "Fashion": (399, 4500),
    "Electronics": (999, 60000),
    "Beauty & Personal Care": (199, 3500),
    "Home & Kitchen": (299, 12000),
}
CATEGORY_WEIGHTS = [0.26, 0.15, 0.20, 0.14, 0.14, 0.11]

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "COD"]
PAYMENT_WEIGHTS = [0.42, 0.20, 0.16, 0.10, 0.12]

# ---------- 1. Customers ----------
customers = []
for i in range(1, N_CUSTOMERS + 1):
    signup_date = START_DATE + timedelta(days=random.randint(0, 700))
    region = random.choice(list(REGIONS.keys()))
    channel = np.random.choice(CHANNELS, p=CHANNEL_WEIGHTS)
    age = int(np.clip(np.random.normal(31, 8), 18, 65))
    customers.append({
        "customer_id": f"CUST{i:05d}",
        "signup_date": signup_date.strftime("%Y-%m-%d"),
        "city": region,
        "region_tier": REGIONS[region],
        "acquisition_channel": channel,
        "age": age,
        "gender": random.choice(["M", "F", "Other"]),
    })
customers_df = pd.DataFrame(customers)

# inject messiness: some null cities, some duplicate customer rows, inconsistent gender casing
dupe_rows = customers_df.sample(60, random_state=1)
customers_df = pd.concat([customers_df, dupe_rows], ignore_index=True)
null_idx = customers_df.sample(frac=0.02, random_state=2).index
customers_df.loc[null_idx, "city"] = None
customers_df.loc[customers_df.sample(frac=0.05, random_state=3).index, "gender"] = \
    customers_df["gender"].sample(frac=0.05, random_state=3).str.lower()

# ---------- 2. Orders (with seasonality + campaign) ----------
# Assign each customer a "purchase propensity" and lifecycle behavior
cust_lookup = customers_df.drop_duplicates("customer_id").set_index("customer_id")

def seasonal_multiplier(date):
    # Festive season boost: Oct-Nov (Diwali), moderate boost Dec (year-end sale), dip in monsoon Jul-Aug
    m = date.month
    if m in (10, 11):
        return 2.4
    if m == 12:
        return 1.5
    if m in (7, 8):
        return 0.7
    if m in (1,):
        return 1.2  # new year
    return 1.0

# Campaign: a flash-discount email campaign run 15 Feb - 28 Feb 2025,
# targeted at a random 50% of customers who signed up before the campaign (A/B holdout design)
campaign_start = datetime(2025, 2, 15)
campaign_end = datetime(2025, 2, 28)
eligible_customers = cust_lookup[cust_lookup["signup_date"] < "2025-02-15"].index.tolist()
treatment_group = set(random.sample(eligible_customers, len(eligible_customers) // 2))
eligible_set = set(eligible_customers)

# Persist the TRUE customer-level assignment (not just orders that happened to occur).
# This is required for an intent-to-treat analysis: customers assigned to treatment/control
# who placed zero orders in the campaign window still belong in the denominator.
def assign_label(cust_id):
    if cust_id not in eligible_set:
        return "not_eligible"
    return "treatment" if cust_id in treatment_group else "control"

customers_df["campaign_assignment"] = customers_df["customer_id"].map(assign_label)

orders = []
order_id = 1
for cust_id, row in cust_lookup.iterrows():
    signup = datetime.strptime(row["signup_date"], "%Y-%m-%d")
    # base monthly purchase probability varies by region tier and channel
    base_p = {"Tier 1": 0.62, "Tier 2": 0.48, "Tier 3": 0.35}[row["region_tier"]]
    # simulate month by month
    cursor = signup
    active = True
    churn_hazard = np.random.uniform(0.03, 0.10)  # monthly chance customer goes dormant
    while cursor <= END_DATE and active:
        days_in_month = 28
        mult = seasonal_multiplier(cursor)
        n_orders_this_month = np.random.poisson(base_p * mult)
        for _ in range(n_orders_this_month):
            order_date = cursor + timedelta(days=random.randint(0, days_in_month - 1))
            if order_date > END_DATE:
                continue
            category = np.random.choice(list(CATEGORIES.keys()), p=CATEGORY_WEIGHTS)
            lo, hi = CATEGORIES[category]
            unit_price = round(np.random.uniform(lo, hi), 2)
            qty = np.random.choice([1, 1, 1, 2, 2, 3], p=[0.45, 0.2, 0.15, 0.1, 0.06, 0.04])

            in_campaign_window = campaign_start <= order_date <= campaign_end
            is_treatment = cust_id in treatment_group
            campaign_flag = "treatment" if (in_campaign_window and is_treatment) else (
                "control" if (in_campaign_window and not is_treatment and cust_id in eligible_customers) else "none"
            )
            discount_pct = 0
            if campaign_flag == "treatment":
                discount_pct = np.random.choice([10, 15, 20], p=[0.5, 0.35, 0.15])
                # treatment group has uplifted order propensity -> simulate via extra order chance below
            elif random.random() < 0.08:
                discount_pct = np.random.choice([5, 10])

            gross = round(unit_price * qty, 2)
            net = round(gross * (1 - discount_pct / 100), 2)
            is_returned = random.random() < (0.11 if category == "Fashion" else 0.045)

            orders.append({
                "order_id": f"ORD{order_id:06d}",
                "customer_id": cust_id,
                "order_date": order_date.strftime("%Y-%m-%d"),
                "product_category": category,
                "quantity": qty,
                "unit_price": unit_price,
                "discount_pct": discount_pct,
                "gross_amount": gross,
                "net_amount": net,
                "payment_method": np.random.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS),
                "city": row["city"],
                "campaign_group": campaign_flag,
                "is_returned": is_returned,
            })
            order_id += 1

        # treatment group gets an extra conversion boost during campaign window
        if cursor.year == 2025 and cursor.month == 2 and cust_id in treatment_group:
            if random.random() < 0.35:
                order_date = campaign_start + timedelta(days=random.randint(0, 13))
                category = np.random.choice(list(CATEGORIES.keys()), p=CATEGORY_WEIGHTS)
                lo, hi = CATEGORIES[category]
                unit_price = round(np.random.uniform(lo, hi), 2)
                qty = 1
                discount_pct = np.random.choice([10, 15, 20], p=[0.5, 0.35, 0.15])
                gross = round(unit_price * qty, 2)
                net = round(gross * (1 - discount_pct / 100), 2)
                orders.append({
                    "order_id": f"ORD{order_id:06d}",
                    "customer_id": cust_id,
                    "order_date": order_date.strftime("%Y-%m-%d"),
                    "product_category": category,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "discount_pct": discount_pct,
                    "gross_amount": gross,
                    "net_amount": net,
                    "payment_method": np.random.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS),
                    "city": row["city"],
                    "campaign_group": "treatment",
                    "is_returned": False,
                })
                order_id += 1

        if random.random() < churn_hazard:
            active = False
        # next month
        cursor = (cursor.replace(day=1) + timedelta(days=32)).replace(day=1)

orders_df = pd.DataFrame(orders)

# inject messiness into orders: duplicate rows, inconsistent payment casing, negative-price typo, nulls
orders_df = pd.concat([orders_df, orders_df.sample(150, random_state=4)], ignore_index=True)
typo_idx = orders_df.sample(20, random_state=5).index
orders_df.loc[typo_idx, "unit_price"] = -orders_df.loc[typo_idx, "unit_price"]
orders_df.loc[orders_df.sample(frac=0.015, random_state=6).index, "city"] = None
orders_df.loc[orders_df.sample(frac=0.01, random_state=7).index, "payment_method"] = "upi"

customers_df.to_csv("raw_customers.csv", index=False)
orders_df.to_csv("raw_orders.csv", index=False)

print(f"Customers (raw, incl. dupes/nulls): {len(customers_df):,}")
print(f"Orders (raw, incl. dupes/typos):    {len(orders_df):,}")
print(f"Treatment group size: {len(treatment_group)} | Eligible pool: {len(eligible_customers)}")
