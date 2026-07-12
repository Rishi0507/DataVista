import pandas as pd

campaign_desc = pd.read_csv("raw/campaign_desc.csv")
campaign_table = pd.read_csv("raw/campaign_table.csv")
coupon_redempt = pd.read_csv("raw/coupon_redempt.csv")

print("=== Campaign types ===")
print(campaign_desc["DESCRIPTION"].value_counts())

print("\n=== Campaign date windows (first 10) ===")
print(campaign_desc.sort_values("START_DAY").head(10))

print("\n=== Households per campaign ===")
recipients_per_campaign = campaign_table.groupby("CAMPAIGN")["household_key"].nunique().sort_values(ascending=False)
print(recipients_per_campaign.head(15))

print("\n=== Redemption rate per campaign (top 15 by recipients) ===")
redeemed_per_campaign = coupon_redempt.groupby("CAMPAIGN")["household_key"].nunique()
summary = pd.DataFrame({
    "recipients": recipients_per_campaign,
    "redeemers": redeemed_per_campaign
}).fillna(0)
summary["redemption_rate_pct"] = round(100 * summary["redeemers"] / summary["recipients"], 1)
summary = summary.merge(campaign_desc.set_index("CAMPAIGN")[["DESCRIPTION","START_DAY","END_DAY"]],
                         left_index=True, right_index=True, how="left")
print(summary.sort_values("recipients", ascending=False).head(15))