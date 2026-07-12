import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
import json

STUDY_START = pd.Timestamp("2016-01-01")
CAMPAIGN_ID = 18
WINDOW_DAYS = 56

campaign_desc = pd.read_csv("raw/campaign_desc.csv")
campaign_table = pd.read_csv("raw/campaign_table.csv")
row = campaign_desc[campaign_desc["CAMPAIGN"] == CAMPAIGN_ID].iloc[0]
window_start = STUDY_START + pd.Timedelta(days=int(row["START_DAY"]))
window_end   = STUDY_START + pd.Timedelta(days=int(row["END_DAY"]))
baseline_end = window_start - pd.Timedelta(days=1)
baseline_start = baseline_end - pd.Timedelta(days=WINDOW_DAYS - 1)

conn = sqlite3.connect("retailpulse_real.db")
all_households = pd.read_sql("SELECT DISTINCT household_key FROM customers", conn)["household_key"].tolist()
recipients = set(campaign_table[campaign_table["CAMPAIGN"] == CAMPAIGN_ID]["household_key"])
non_recipients = set(all_households) - recipients

def rev_by_household(start, end):
    df = pd.read_sql(f"""
        SELECT household_key, SUM(gross_sales_value) AS revenue FROM baskets
        WHERE order_date BETWEEN '{start.date()}' AND '{end.date()}' GROUP BY household_key
    """, conn)
    return dict(zip(df.household_key, df.revenue))

during_map = rev_by_household(window_start, window_end)
base_map = rev_by_household(baseline_start, baseline_end)

def deltas(group):
    return np.array([during_map.get(h,0.0) - base_map.get(h,0.0) for h in group])

treat_delta = deltas(recipients)
ctrl_delta = deltas(non_recipients)

did_t, did_p = stats.ttest_ind(treat_delta, ctrl_delta, equal_var=False)
did_estimate = treat_delta.mean() - ctrl_delta.mean()

treat_during, treat_base = np.mean([during_map.get(h,0.0) for h in recipients]), np.mean([base_map.get(h,0.0) for h in recipients])
ctrl_during, ctrl_base = np.mean([during_map.get(h,0.0) for h in non_recipients]), np.mean([base_map.get(h,0.0) for h in non_recipients])
raw_uplift_pct = round(100*(treat_during-ctrl_during)/ctrl_during, 1)
baseline_gap_pct = round(100*(treat_base-ctrl_base)/ctrl_base, 1)

did_significant = did_p < 0.05
did_positive = did_estimate > 0

if did_significant and did_positive:
    stamp = "SIGNIFICANT INCREMENTAL LIFT"
    title = f"Verdict: Campaign 18 shows a real, if modest, incremental lift once pre-existing spend is controlled for."
elif did_significant and not did_positive:
    stamp = "NO EVIDENCE OF LIFT"
    title = "Verdict: the raw uplift is an illusion — recipients already outspent non-recipients before the campaign, and the gap did not grow."
else:
    stamp = "INCONCLUSIVE"
    title = "Verdict: no statistically significant incremental effect detected once pre-existing spend differences are controlled for."

body = (
    f"Recipients already outspent non-recipients by {baseline_gap_pct}% BEFORE Campaign 18 began "
    f"(${treat_base:,.0f} vs ${ctrl_base:,.0f} per household) — consistent with Dunnhumby's documentation "
    f"that TypeA campaigns are targeted using prior purchase behavior, not randomly assigned. "
    f"The raw campaign-window comparison shows a {raw_uplift_pct}% gap, which naively looks like a huge "
    f"effect, but a difference-in-differences test (each household's own change in spend, recipients vs. "
    f"non-recipients) shows an estimated incremental effect of ${did_estimate:,.2f} per household "
    f"(t={did_t:.3f}, p={did_p:.4f}), which is {'statistically significant' if did_significant else 'not statistically significant'}. "
    f"Recommendation: {'the campaign appears to provide a genuine, if modest, incremental lift and can be cautiously scaled with a proper randomized holdout to confirm.' if (did_significant and did_positive) else 'this campaign looks like efficient targeting of already-high-value households rather than demand generation — real business value, but not evidence the campaign itself drives incremental spend. A randomized holdout test is needed before crediting the campaign with causing revenue.'}"
)

summary = {
    "campaign_id": CAMPAIGN_ID,
    "window_start": str(window_start.date()), "window_end": str(window_end.date()),
    "baseline_start": str(baseline_start.date()), "baseline_end": str(baseline_end.date()),
    "recipients": len(recipients), "non_recipients": len(non_recipients),
    "treatment_avg_revenue": round(treat_during,2), "control_avg_revenue": round(ctrl_during,2),
    "treatment_baseline_avg_revenue": round(treat_base,2), "control_baseline_avg_revenue": round(ctrl_base,2),
    "raw_uplift_pct": raw_uplift_pct, "baseline_gap_pct": baseline_gap_pct,
    "did_estimate": round(did_estimate,2), "did_t_statistic": round(float(did_t),3),
    "did_p_value": "<0.001" if did_p<0.001 else round(float(did_p),5),
    "did_significant": bool(did_significant),
    "treatment_conversion_rate_pct": round(100*np.mean([during_map.get(h,0)>0 for h in recipients]),1),
    "control_conversion_rate_pct": round(100*np.mean([during_map.get(h,0)>0 for h in non_recipients]),1),
    "significant_at_95": bool(did_significant),
    "verdict_stamp": stamp, "verdict_title": title, "verdict_body": body,
    "note": "Recipients not randomly assigned (TypeA campaigns targeted by prior purchase behavior). Raw comparison is confounded; difference-in-differences used to isolate incremental effect."
}

with open("campaign_summary.json","w") as f: json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
conn.close()