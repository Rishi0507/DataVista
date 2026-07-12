-- Revenue & basket KPIs by year
SELECT strftime('%Y', order_date) AS order_year,
       COUNT(DISTINCT BASKET_ID) AS total_baskets,
       COUNT(DISTINCT household_key) AS active_households,
       ROUND(SUM(gross_sales_value),2) AS net_revenue,
       ROUND(SUM(gross_sales_value)*1.0/COUNT(DISTINCT BASKET_ID),2) AS avg_basket_value
FROM baskets GROUP BY order_year ORDER BY order_year;

-- Monthly revenue trend
SELECT strftime('%Y-%m', order_date) AS ym, ROUND(SUM(gross_sales_value),2) AS revenue
FROM baskets GROUP BY ym ORDER BY ym;

-- RFM segmentation (NTILE quintiles)
WITH last_date AS (SELECT MAX(order_date) AS max_dt FROM baskets),
rfm_base AS (
    SELECT household_key,
        CAST(julianday((SELECT max_dt FROM last_date)) - julianday(MAX(order_date)) AS INT) AS recency_days,
        COUNT(DISTINCT BASKET_ID) AS frequency,
        ROUND(SUM(gross_sales_value),2) AS monetary
    FROM baskets GROUP BY household_key
)
SELECT *,
    NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
    NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
    NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
FROM rfm_base ORDER BY monetary DESC;

-- Cohort retention (first-basket-date proxy for signup)
WITH first_purchase AS (SELECT household_key, MIN(order_date) AS first_date FROM baskets GROUP BY household_key),
cohort AS (SELECT household_key, strftime('%Y-%m', first_date) AS cohort_month FROM first_purchase),
activity AS (
    SELECT b.household_key, c.cohort_month,
       (CAST(strftime('%Y', b.order_date) AS INT) - CAST(substr(c.cohort_month,1,4) AS INT)) * 12
        + (CAST(strftime('%m', b.order_date) AS INT) - CAST(substr(c.cohort_month,6,2) AS INT)) AS month_index
    FROM baskets b JOIN cohort c ON b.household_key = c.household_key
),
cohort_size AS (SELECT cohort_month, COUNT(DISTINCT household_key) AS n FROM cohort GROUP BY cohort_month),
per_cohort AS (
    SELECT a.cohort_month, a.month_index, COUNT(DISTINCT a.household_key) AS active, cs.n
    FROM activity a JOIN cohort_size cs ON a.cohort_month = cs.cohort_month
    WHERE a.month_index BETWEEN 0 AND 6
    GROUP BY a.cohort_month, a.month_index
)
SELECT month_index, SUM(active) AS total_active, SUM(n) AS total_cohort_n,
       ROUND(100.0*SUM(active)/SUM(n),1) AS retention_pct
FROM per_cohort GROUP BY month_index ORDER BY month_index;

-- Campaign 18 — intent-to-treat (see 05_campaign_analysis.py for full stats)
-- Recipients are NOT randomly assigned in real data; this is associational.
SELECT
    CASE WHEN c.household_key IN (SELECT household_key FROM campaign_table WHERE CAMPAIGN = 18)
         THEN 'recipient' ELSE 'non_recipient' END AS group_label,
    COUNT(DISTINCT c.household_key) AS households,
    ROUND(SUM(COALESCE(b.gross_sales_value,0)),2) AS total_revenue
FROM customers c
LEFT JOIN baskets b ON c.household_key = b.household_key
    AND b.order_date BETWEEN '2017-08-10' AND '2017-10-04'  -- Campaign 18 window
GROUP BY group_label;

-- Department (category) performance
SELECT DEPARTMENT, COUNT(*) AS line_items, ROUND(SUM(SALES_VALUE),2) AS revenue,
       ROUND(AVG(SALES_VALUE),2) AS avg_line_value
FROM basket_items GROUP BY DEPARTMENT ORDER BY revenue DESC;

-- Store performance (replaces acquisition-channel efficiency; real data
-- has no channel dimension, but does have genuine store-level data)
SELECT store_id, COUNT(DISTINCT household_key) AS households,
       ROUND(SUM(gross_sales_value),2) AS total_revenue,
       ROUND(SUM(gross_sales_value)/COUNT(DISTINCT household_key),2) AS revenue_per_household
FROM baskets GROUP BY store_id ORDER BY total_revenue DESC LIMIT 20;