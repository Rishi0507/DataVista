"""
RetailPulse — analysis runner.
Executes the SQL layer, adds statistical rigor (t-test + confidence interval
on the campaign result, not just "treatment revenue > control revenue"),
and exports clean JSON for the dashboard.
"""
import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
import json

conn = sqlite3.connect("retailpulse.db")

# ---------- KPIs ----------
kpi = pd.read_sql("""
SELECT strftime('%Y', order_date) AS order_year,
       COUNT(DISTINCT order_id) AS total_orders,
       COUNT(DISTINCT customer_id) AS active_customers,
       ROUND(SUM(net_amount),2) AS net_revenue,
       ROUND(SUM(net_amount)*1.0/COUNT(DISTINCT order_id),2) AS avg_order_value
FROM orders WHERE is_returned = 0 GROUP BY order_year ORDER BY order_year
""", conn)

monthly = pd.read_sql("""
SELECT strftime('%Y-%m', order_date) AS ym, ROUND(SUM(net_amount),2) AS revenue
FROM orders WHERE is_returned = 0 GROUP BY ym ORDER BY ym
""", conn)

# ---------- RFM ----------
rfm = pd.read_sql("""
WITH last_date AS (SELECT MAX(order_date) AS max_dt FROM orders),
rfm_base AS (
    SELECT o.customer_id,
        CAST(julianday((SELECT max_dt FROM last_date)) - julianday(MAX(o.order_date)) AS INT) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(o.net_amount),2) AS monetary
    FROM orders o WHERE o.is_returned = 0 GROUP BY o.customer_id
),
rfm_scored AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm_base
)
SELECT *,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 4 AND f_score >= 3 THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'New / Promising'
        WHEN r_score <= 2 AND f_score >= 4 THEN 'At Risk (high value)'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Hibernating'
        ELSE 'Needs Attention'
    END AS rfm_segment
FROM rfm_scored
""", conn)

rfm_rollup = rfm.groupby("rfm_segment").agg(
    customers=("customer_id", "count"),
    avg_ltv=("monetary", "mean"),
    segment_revenue=("monetary", "sum")
).round(0).reset_index().sort_values("segment_revenue", ascending=False)

# ---------- Cohort retention ----------
cohort = pd.read_sql("""
WITH cohort AS (SELECT customer_id, strftime('%Y-%m', signup_date) AS cohort_month FROM customers),
activity AS (
    SELECT o.customer_id, c.cohort_month, strftime('%Y-%m', o.order_date) AS order_month,
       (CAST(strftime('%Y', o.order_date) AS INT) - CAST(substr(c.cohort_month,1,4) AS INT)) * 12
        + (CAST(strftime('%m', o.order_date) AS INT) - CAST(substr(c.cohort_month,6,2) AS INT)) AS month_index
    FROM orders o JOIN cohort c ON o.customer_id = c.customer_id
),
cohort_size AS (SELECT cohort_month, COUNT(DISTINCT customer_id) AS n_customers FROM cohort GROUP BY cohort_month)
SELECT a.cohort_month, a.month_index, COUNT(DISTINCT a.customer_id) AS active_customers,
       cs.n_customers, ROUND(100.0*COUNT(DISTINCT a.customer_id)/cs.n_customers,1) AS retention_pct
FROM activity a JOIN cohort_size cs ON a.cohort_month = cs.cohort_month
WHERE a.month_index BETWEEN 0 AND 6
GROUP BY a.cohort_month, a.month_index ORDER BY a.cohort_month, a.month_index
""", conn)

# Average retention curve across all cohorts (cleaner for a dashboard headline)
avg_retention = cohort.groupby("month_index").apply(
    lambda g: round(100 * (g["active_customers"] * g["n_customers"]).sum() / (g["n_customers"]**2).sum(), 1)
    if False else round((g["active_customers"].sum() / g["n_customers"].sum()) * 100, 1)
).reset_index(name="retention_pct")

# ---------- Campaign A/B test (Intent-to-Treat) ----------
# IMPORTANT: the assignment groups are the customers who were ASSIGNED treatment/control at
# randomization time (stored on the customers table), NOT just the ones who happened to place
# an order in the campaign window. Restricting to "customers who ordered" conditions on a
# post-treatment outcome (conversion) and biases the comparison -- classic intent-to-treat
# violation. Every assigned customer must be in the denominator, with revenue = 0 if they
# didn't purchase.
assignment = pd.read_sql("""
SELECT customer_id, campaign_assignment FROM customers
WHERE campaign_assignment IN ('treatment','control')
""", conn)

window_orders = pd.read_sql("""
SELECT customer_id, SUM(net_amount) AS revenue
FROM orders
WHERE order_date BETWEEN '2025-02-15' AND '2025-02-28'
GROUP BY customer_id
""", conn)

itt = assignment.merge(window_orders, on="customer_id", how="left")
itt["revenue"] = itt["revenue"].fillna(0.0)
itt["converted"] = itt["revenue"] > 0

treatment_rev = itt[itt.campaign_assignment == "treatment"]["revenue"]
control_rev = itt[itt.campaign_assignment == "control"]["revenue"]

t_stat, p_value = stats.ttest_ind(treatment_rev, control_rev, equal_var=False)

def ci_95(series):
    m = series.mean()
    se = series.std(ddof=1) / np.sqrt(len(series))
    return m - 1.96 * se, m + 1.96 * se

t_lo, t_hi = ci_95(treatment_rev)
c_lo, c_hi = ci_95(control_rev)

treat_conv_rate = itt[itt.campaign_assignment == "treatment"]["converted"].mean()
control_conv_rate = itt[itt.campaign_assignment == "control"]["converted"].mean()
conv_chi2, conv_p, _, _ = stats.chi2_contingency(pd.crosstab(itt.campaign_assignment, itt.converted))

campaign_summary = {
    "treatment_customers": int((itt.campaign_assignment == "treatment").sum()),
    "control_customers": int((itt.campaign_assignment == "control").sum()),
    "treatment_avg_revenue": round(treatment_rev.mean(), 2),
    "control_avg_revenue": round(control_rev.mean(), 2),
    "treatment_ci_95": [round(t_lo, 2), round(t_hi, 2)],
    "control_ci_95": [round(c_lo, 2), round(c_hi, 2)],
    "uplift_pct": round(100 * (treatment_rev.mean() - control_rev.mean()) / control_rev.mean(), 1),
    "t_statistic": round(float(t_stat), 3),
    "p_value": round(float(p_value), 5),
    "significant_at_95": bool(p_value < 0.05),
    "treatment_conversion_rate_pct": round(treat_conv_rate * 100, 1),
    "control_conversion_rate_pct": round(control_conv_rate * 100, 1),
    "conversion_chi2": round(float(conv_chi2), 2),
    "conversion_p_value": round(float(conv_p), 6),
}

# ---------- Category / region ----------
category_region = pd.read_sql("""
SELECT c.region_tier, o.product_category,
       COUNT(o.order_id) AS orders, ROUND(SUM(o.net_amount),2) AS revenue,
       ROUND(AVG(o.net_amount),2) AS avg_order_value,
       ROUND(100.0*SUM(CASE WHEN o.is_returned THEN 1 ELSE 0 END)/COUNT(*),2) AS return_rate_pct
FROM orders o JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.region_tier, o.product_category
ORDER BY c.region_tier, revenue DESC
""", conn)

channel_perf = pd.read_sql("""
SELECT c.acquisition_channel,
       COUNT(DISTINCT c.customer_id) AS customers_acquired,
       ROUND(SUM(o.net_amount),2) AS total_revenue,
       ROUND(SUM(o.net_amount)/COUNT(DISTINCT c.customer_id),2) AS revenue_per_customer
FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.is_returned = 0
GROUP BY c.acquisition_channel ORDER BY revenue_per_customer DESC
""", conn)

category_total = pd.read_sql("""
SELECT product_category, ROUND(SUM(net_amount),2) AS revenue, COUNT(*) AS orders
FROM orders WHERE is_returned = 0 GROUP BY product_category ORDER BY revenue DESC
""", conn)

# ---------- Export ----------
export = {
    "kpi_by_year": kpi.to_dict(orient="records"),
    "monthly_revenue": monthly.to_dict(orient="records"),
    "rfm_rollup": rfm_rollup.to_dict(orient="records"),
    "avg_retention_curve": avg_retention.to_dict(orient="records"),
    "campaign_ab_test": campaign_summary,
    "category_region": category_region.to_dict(orient="records"),
    "channel_performance": channel_perf.to_dict(orient="records"),
    "category_total": category_total.to_dict(orient="records"),
    "totals": {
        "total_customers": int(pd.read_sql("SELECT COUNT(*) c FROM customers", conn).iloc[0,0]),
        "total_orders": int(pd.read_sql("SELECT COUNT(*) c FROM orders WHERE is_returned=0", conn).iloc[0,0]),
        "total_revenue": round(pd.read_sql("SELECT SUM(net_amount) r FROM orders WHERE is_returned=0", conn).iloc[0,0], 2),
        "return_rate_pct": round(pd.read_sql("SELECT 100.0*SUM(is_returned)/COUNT(*) r FROM orders", conn).iloc[0,0], 2),
    }
}

with open("dashboard_data.json", "w") as f:
    json.dump(export, f, indent=2)

print("=== KPI by year ===")
print(kpi.to_string(index=False))
print("\n=== RFM segment rollup ===")
print(rfm_rollup.to_string(index=False))
print("\n=== Avg retention curve (month 0-6) ===")
print(avg_retention.to_string(index=False))
print("\n=== Campaign A/B test ===")
print(json.dumps(campaign_summary, indent=2))
print("\n=== Totals ===")
print(json.dumps(export["totals"], indent=2))

conn.close()
