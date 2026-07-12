import sqlite3
import pandas as pd
import numpy as np
from scipy import stats

STUDY_START = pd.Timestamp("2016-01-01")
CAMPAIGN_ID = 18
WINDOW_DAYS = 56  

campaign_table = pd.read_csv("raw/campaign_table.csv")
window_start = pd.Timestamp("2017-08-10")
baseline_end = window_start - pd.Timedelta(days=1)
baseline_start = baseline_end - pd.Timedelta(days=WINDOW_DAYS - 1)

print(f"Baseline window (pre-campaign): {baseline_start.date()} to {baseline_end.date()}")

conn = sqlite3.connect("retailpulse_real.db")
all_households = pd.read_sql("SELECT DISTINCT household_key FROM customers", conn)["household_key"].tolist()
recipients = set(campaign_table[campaign_table["CAMPAIGN"] == CAMPAIGN_ID]["household_key"])
non_recipients = set(all_households) - recipients

baseline = pd.read_sql(f"""
    SELECT household_key, SUM(gross_sales_value) AS revenue
    FROM baskets
    WHERE order_date BETWEEN '{baseline_start.date()}' AND '{baseline_end.date()}'
    GROUP BY household_key
""", conn)
rev_map = dict(zip(baseline.household_key, baseline.revenue))

treat_base = np.array([rev_map.get(h, 0.0) for h in recipients])
ctrl_base  = np.array([rev_map.get(h, 0.0) for h in non_recipients])

t_stat, p_value = stats.ttest_ind(treat_base, ctrl_base, equal_var=False)
baseline_gap_pct = round(100 * (treat_base.mean() - ctrl_base.mean()) / ctrl_base.mean(), 1)

print(f"Recipients baseline avg revenue:     {treat_base.mean():.2f}")
print(f"Non-recipients baseline avg revenue: {ctrl_base.mean():.2f}")
print(f"Pre-campaign gap: {baseline_gap_pct}% (t={t_stat:.3f}, p={p_value:.5f})")
print(f"\nCompare to campaign-window uplift of 196.7% from 05_campaign_analysis.py.")
print("If this baseline gap is close to 196.7%, most of the effect is pre-existing spend level, not campaign impact.")
conn.close()