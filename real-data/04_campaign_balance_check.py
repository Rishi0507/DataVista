import pandas as pd

CAMPAIGN_ID = 18

campaign_table = pd.read_csv("raw/campaign_table.csv")
hh_demo = pd.read_csv("raw/hh_demographic.csv")

recipients = set(campaign_table[campaign_table["CAMPAIGN"] == CAMPAIGN_ID]["household_key"])
all_households = set(pd.read_csv("raw/transaction_data.csv", usecols=["household_key"])["household_key"].unique())
non_recipients = all_households - recipients

print(f"Campaign {CAMPAIGN_ID}: {len(recipients)} recipients, {len(non_recipients)} non-recipients")

demo = hh_demo.copy()
demo["group"] = demo["household_key"].apply(
    lambda h: "recipient" if h in recipients else ("non_recipient" if h in non_recipients else "other")
)
demo_known = demo[demo["group"].isin(["recipient", "non_recipient"])]

print(f"\nHouseholds with demographics in either group: {len(demo_known)} "
      f"(of {len(recipients)+len(non_recipients)} total -- most won't have demo data, expected)")

for col in ["INCOME_DESC", "HOUSEHOLD_SIZE_DESC", "HOMEOWNER_DESC", "AGE_DESC"]:
    print(f"\n=== {col} distribution by group (%) ===")
    ct = pd.crosstab(demo_known["group"], demo_known[col], normalize="index") * 100
    print(ct.round(1))