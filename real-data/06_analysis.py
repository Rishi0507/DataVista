import sqlite3
import pandas as pd
import json

conn = sqlite3.connect("retailpulse_real.db")

kpi = pd.read_sql("""
SELECT strftime('%Y', order_date) AS order_year,
       COUNT(DISTINCT BASKET_ID) AS total_baskets,
       COUNT(DISTINCT household_key) AS active_households,
       ROUND(SUM(gross_sales_value),2) AS net_revenue,
       ROUND(SUM(gross_sales_value)*1.0/COUNT(DISTINCT BASKET_ID),2) AS avg_basket_value
FROM baskets GROUP BY order_year ORDER BY order_year
""", conn)

monthly = pd.read_sql("""
SELECT strftime('%Y-%m', order_date) AS ym, ROUND(SUM(gross_sales_value),2) AS revenue
FROM baskets GROUP BY ym ORDER BY ym
""", conn)

rfm = pd.read_sql("""
WITH last_date AS (SELECT MAX(order_date) AS max_dt FROM baskets),
rfm_base AS (
    SELECT household_key,
        CAST(julianday((SELECT max_dt FROM last_date)) - julianday(MAX(order_date)) AS INT) AS recency_days,
        COUNT(DISTINCT BASKET_ID) AS frequency,
        ROUND(SUM(gross_sales_value),2) AS monetary
    FROM baskets GROUP BY household_key
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
    customers=("household_key","count"), avg_ltv=("monetary","mean"), segment_revenue=("monetary","sum")
).round(0).reset_index().sort_values("segment_revenue", ascending=False)


cohort = pd.read_sql("""
WITH first_purchase AS (
    SELECT household_key, MIN(order_date) AS first_date FROM baskets GROUP BY household_key
),
cohort AS (
    SELECT household_key, strftime('%Y-%m', first_date) AS cohort_month FROM first_purchase
),
activity AS (
    SELECT b.household_key, c.cohort_month,
       (CAST(strftime('%Y', b.order_date) AS INT) - CAST(substr(c.cohort_month,1,4) AS INT)) * 12
        + (CAST(strftime('%m', b.order_date) AS INT) - CAST(substr(c.cohort_month,6,2) AS INT)) AS month_index
    FROM baskets b JOIN cohort c ON b.household_key = c.household_key
),
cohort_size AS (SELECT cohort_month, COUNT(DISTINCT household_key) AS n FROM cohort GROUP BY cohort_month)
SELECT a.cohort_month, a.month_index, COUNT(DISTINCT a.household_key) AS active, cs.n
FROM activity a JOIN cohort_size cs ON a.cohort_month = cs.cohort_month
WHERE a.month_index BETWEEN 0 AND 6
GROUP BY a.cohort_month, a.month_index
""", conn)

avg_retention = cohort.groupby("month_index").apply(
    lambda g: round(100 * g["active"].sum() / g["n"].sum(), 1), include_groups=False
).reset_index(name="retention_pct")

category = pd.read_sql("""
SELECT DEPARTMENT, COUNT(*) AS line_items,
       ROUND(SUM(SALES_VALUE),2) AS revenue,
       ROUND(AVG(SALES_VALUE),2) AS avg_line_value
FROM basket_items GROUP BY DEPARTMENT ORDER BY revenue DESC
""", conn)


store_perf = pd.read_sql("""
SELECT store_id, COUNT(DISTINCT household_key) AS households,
       ROUND(SUM(gross_sales_value),2) AS total_revenue,
       ROUND(SUM(gross_sales_value)/COUNT(DISTINCT household_key),2) AS revenue_per_household
FROM baskets GROUP BY store_id ORDER BY total_revenue DESC LIMIT 20
""", conn)

with open("campaign_summary.json") as f:
    campaign_summary = json.load(f)

totals = {
    "total_customers": int(pd.read_sql("SELECT COUNT(*) c FROM customers", conn).iloc[0,0]),
    "total_baskets": int(pd.read_sql("SELECT COUNT(*) c FROM baskets", conn).iloc[0,0]),
    "total_revenue": round(pd.read_sql("SELECT SUM(gross_sales_value) r FROM baskets", conn).iloc[0,0], 2),
    "demographics_coverage_pct": round(100 * pd.read_sql(
        "SELECT SUM(CASE WHEN AGE_DESC != 'Unknown' THEN 1 ELSE 0 END)*1.0/COUNT(*) c FROM customers", conn
    ).iloc[0,0], 1),
}

export = {
    "kpi_by_year": kpi.to_dict(orient="records"),
    "monthly_revenue": monthly.to_dict(orient="records"),
    "rfm_rollup": rfm_rollup.to_dict(orient="records"),
    "avg_retention_curve": avg_retention.to_dict(orient="records"),
    "campaign_ab_test": campaign_summary,
    "category_breakdown": category.to_dict(orient="records"),
    "store_performance": store_perf.to_dict(orient="records"),
    "totals": totals,
}

with open("dashboard_data_real.json", "w") as f:
    json.dump(export, f, indent=2)

print("=== KPI by year ===")
print(kpi.to_string(index=False))
print("\n=== RFM rollup ===")
print(rfm_rollup.to_string(index=False))
print("\n=== Retention curve ===")
print(avg_retention.to_string(index=False))
print("\n=== Totals ===")
print(json.dumps(totals, indent=2))
conn.close()