-- ============================================================
-- RetailPulse Analytics — Core SQL Queries
-- Database: retailpulse.db (SQLite)
-- Tables: customers(customer_id, signup_date, city, region_tier,
--                    acquisition_channel, age, gender)
--         orders(order_id, customer_id, order_date, product_category,
--                quantity, unit_price, discount_pct, gross_amount,
--                net_amount, payment_method, city, campaign_group, is_returned)
-- ============================================================

-- ------------------------------------------------------------
-- 1. Revenue & order KPIs, Year-over-Year
-- ------------------------------------------------------------
SELECT
    strftime('%Y', order_date)                         AS order_year,
    COUNT(DISTINCT order_id)                            AS total_orders,
    COUNT(DISTINCT customer_id)                         AS active_customers,
    ROUND(SUM(net_amount), 2)                           AS net_revenue,
    ROUND(SUM(net_amount) * 1.0 / COUNT(DISTINCT order_id), 2) AS avg_order_value
FROM orders
WHERE is_returned = 0
GROUP BY order_year
ORDER BY order_year;

-- ------------------------------------------------------------
-- 2. Monthly revenue trend with month-over-month growth %
-- ------------------------------------------------------------
WITH monthly AS (
    SELECT strftime('%Y-%m', order_date) AS ym,
           ROUND(SUM(net_amount), 2) AS revenue
    FROM orders
    WHERE is_returned = 0
    GROUP BY ym
)
SELECT ym, revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY ym))
             / NULLIF(LAG(revenue) OVER (ORDER BY ym), 0), 1) AS mom_growth_pct
FROM monthly
ORDER BY ym;

-- ------------------------------------------------------------
-- 3. RFM Segmentation (Recency, Frequency, Monetary)
--    Scores each customer 1-5 on each dimension via NTILE quintiles,
--    then buckets them into standard lifecycle segments.
-- ------------------------------------------------------------
WITH last_date AS (SELECT MAX(order_date) AS max_dt FROM orders),
rfm_base AS (
    SELECT
        o.customer_id,
        CAST(julianday((SELECT max_dt FROM last_date)) - julianday(MAX(o.order_date)) AS INT) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(o.net_amount), 2) AS monetary
    FROM orders o
    WHERE o.is_returned = 0
    GROUP BY o.customer_id
),
rfm_scored AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,   -- lower recency_days = more recent = higher score
        NTILE(5) OVER (ORDER BY frequency ASC)     AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)      AS m_score
    FROM rfm_base
)
SELECT
    customer_id, recency_days, frequency, monetary, r_score, f_score, m_score,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 4 AND f_score >= 3                  THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2                  THEN 'New / Promising'
        WHEN r_score <= 2 AND f_score >= 4                  THEN 'At Risk (high value)'
        WHEN r_score <= 2 AND f_score <= 2                  THEN 'Hibernating'
        ELSE 'Needs Attention'
    END AS rfm_segment
FROM rfm_scored
ORDER BY monetary DESC;

-- ------------------------------------------------------------
-- 4. Segment-level rollup (what the dashboard actually shows)
-- ------------------------------------------------------------
-- (wrap query 3 as a CTE named rfm_segments, then:)
-- SELECT rfm_segment, COUNT(*) AS customers, ROUND(AVG(monetary),0) AS avg_ltv,
--        ROUND(SUM(monetary),0) AS segment_revenue
-- FROM rfm_segments GROUP BY rfm_segment ORDER BY segment_revenue DESC;

-- ------------------------------------------------------------
-- 5. Cohort retention — % of each signup-month cohort still
--    ordering N months later
-- ------------------------------------------------------------
WITH cohort AS (
    SELECT customer_id, strftime('%Y-%m', signup_date) AS cohort_month
    FROM customers
),
activity AS (
    SELECT o.customer_id,
           c.cohort_month,
           strftime('%Y-%m', o.order_date) AS order_month,
           (CAST(strftime('%Y', o.order_date) AS INT) - CAST(substr(c.cohort_month,1,4) AS INT)) * 12
             + (CAST(strftime('%m', o.order_date) AS INT) - CAST(substr(c.cohort_month,6,2) AS INT)) AS month_index
    FROM orders o
    JOIN cohort c ON o.customer_id = c.customer_id
),
cohort_size AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS n_customers
    FROM cohort GROUP BY cohort_month
)
SELECT a.cohort_month, a.month_index,
       COUNT(DISTINCT a.customer_id) AS active_customers,
       cs.n_customers,
       ROUND(100.0 * COUNT(DISTINCT a.customer_id) / cs.n_customers, 1) AS retention_pct
FROM activity a
JOIN cohort_size cs ON a.cohort_month = cs.cohort_month
WHERE a.month_index BETWEEN 0 AND 6
GROUP BY a.cohort_month, a.month_index
ORDER BY a.cohort_month, a.month_index;

-- ------------------------------------------------------------
-- 6. Campaign performance — Feb 2025 flash-discount A/B test
--    Intent-to-treat: denominator is every customer ASSIGNED to
--    treatment/control at randomization time (customers.campaign_assignment),
--    not just the ones who happened to place an order in the window.
--    Conditioning on "placed an order" would bias this toward whoever
--    was already going to buy -- a classic post-treatment selection bug.
-- ------------------------------------------------------------
WITH window_orders AS (
    SELECT customer_id, SUM(net_amount) AS revenue
    FROM orders
    WHERE order_date BETWEEN '2025-02-15' AND '2025-02-28'
    GROUP BY customer_id
)
SELECT
    c.campaign_assignment,
    COUNT(*)                                              AS assigned_customers,
    SUM(CASE WHEN w.revenue IS NOT NULL THEN 1 ELSE 0 END) AS converted_customers,
    ROUND(100.0 * SUM(CASE WHEN w.revenue IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS conversion_rate_pct,
    ROUND(SUM(COALESCE(w.revenue, 0)), 2)                 AS total_revenue,
    ROUND(SUM(COALESCE(w.revenue, 0)) / COUNT(*), 2)       AS revenue_per_assigned_customer
FROM customers c
LEFT JOIN window_orders w ON c.customer_id = w.customer_id
WHERE c.campaign_assignment IN ('treatment', 'control')
GROUP BY c.campaign_assignment;

-- ------------------------------------------------------------
-- 7. Category performance by region tier
-- ------------------------------------------------------------
SELECT
    c.region_tier,
    o.product_category,
    COUNT(o.order_id) AS orders,
    ROUND(SUM(o.net_amount), 2) AS revenue,
    ROUND(AVG(o.net_amount), 2) AS avg_order_value,
    ROUND(100.0 * SUM(CASE WHEN o.is_returned THEN 1 ELSE 0 END) / COUNT(*), 2) AS return_rate_pct
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.region_tier, o.product_category
ORDER BY c.region_tier, revenue DESC;

-- ------------------------------------------------------------
-- 8. Acquisition channel efficiency — revenue & LTV per channel
-- ------------------------------------------------------------
SELECT
    c.acquisition_channel,
    COUNT(DISTINCT c.customer_id) AS customers_acquired,
    ROUND(SUM(o.net_amount), 2) AS total_revenue,
    ROUND(SUM(o.net_amount) / COUNT(DISTINCT c.customer_id), 2) AS revenue_per_customer
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.is_returned = 0
GROUP BY c.acquisition_channel
ORDER BY revenue_per_customer DESC;
