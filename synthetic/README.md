# DataVista: End-to-End Customer and Sales Analytics

A full analytics case study for a simulated mid-size Indian e-commerce retailer: raw data,
cleaned into a SQL warehouse, then taken through segmentation, retention, and A/B testing, into a
BI dashboard and a set of business recommendations.

This project was built to demonstrate the complete analyst workflow, not just a notebook of
charts:

```
messy raw data -> ETL/cleaning -> SQL warehouse -> SQL analysis -> statistical testing -> dashboard -> business recommendation
```

## 1. Business context

DataVista is a simulated online retailer selling across 6 categories (Mobiles, Electronics, Home
Appliances, Fashion, Home and Kitchen, Beauty) to customers across Tier 1, 2, and 3 Indian cities.
The dataset spans January 2024 to December 2025: 6,000 customers and 33,670 cleaned transactions
(31,718 net of the 1,952 returned orders; see note below), generated with realistic seasonality
(festive season spikes), churn behavior, and a real marketing experiment.

> **Order count note:** two different order counts appear throughout this project on purpose, not
> by mistake. 33,670 is the total number of cleaned orders in the warehouse, and 31,718 is that
> number net of the 1,952 (5.8%) that were returned, which is what feeds the revenue KPIs. Any
> bullet or chart quoting "orders" should specify which one.

Data is synthetic, generated programmatically with deliberate business logic, seasonality, and
realistic messiness, since no proprietary retailer dataset was available. The SQL, statistics, and
dashboard work are the same as would be run against a real warehouse.

## 2. Data and tools

| Layer | Tool |
|---|---|
| Data generation | Python (pandas, numpy, Faker) |
| Cleaning / ETL | Python (pandas) |
| Warehouse | SQLite |
| Analysis | SQL (window functions, CTEs) and Python (pandas, SciPy) |
| Statistical testing | SciPy (Welch's t-test, 95% confidence intervals) |
| Dashboard | HTML/CSS/JS and Chart.js |

## 3. Pipeline

### Step 1: Generate and inject realistic messiness (`01_generate_data.py`)
Simulates 2 years of orders with seasonality (2.4x order volume in October to November festive
season, monsoon dip in July to August), 5 acquisition channels, and a real randomized marketing
campaign. Deliberately injects duplicate rows, null cities, inconsistent casing, and a sign-error
bug in pricing: the same categories of dirty data every analyst encounters.

### Step 2: Clean and load (`02_clean_and_load.py`)
- Deduplicated 60 customer rows and 150 order rows
- Standardized inconsistent categorical values (gender, payment method casing)
- Caught and corrected 20 negative-price records (a data-entry sign error), recalculating all
  dependent fields
- Filled missing city values, validated referential integrity between orders and customers
- Loaded into an indexed SQLite warehouse

Full log in `cleaning_log.txt`.

### Step 3: SQL analysis (`03_analysis_queries.sql`)
Eight analytical queries written directly in SQL, not just pandas, including:
- RFM segmentation via `NTILE()` window functions, scoring every customer on Recency, Frequency,
  and Monetary value, and bucketing into 6 lifecycle segments
- Cohort retention using self-joins and date math, to track the percentage of each signup cohort
  still active N months later
- Campaign performance comparing treatment vs. control groups
- Year-over-year and month-over-month growth using `LAG()` window functions
- Category by region-tier performance, and acquisition channel efficiency

### Step 4: Statistical testing (`04_analysis.py`)
The marketing team ran a flash-discount campaign (10 to 20% off) emailed to a random 50% of
eligible customers in February 2025, a genuine randomized control/treatment split. The comparison
is done intent-to-treat: every customer assigned to treatment or control is included in the
analysis (1,761 vs. 1,762), including those who did not purchase anything, with revenue recorded
as 0 for non-purchasers. This runs a Welch's two-sample t-test with 95% confidence intervals, plus
a chi-square test on conversion rate, to check whether the difference is real or noise.

An earlier version of this analysis only counted customers who placed an order in the campaign
window, a post-treatment selection bug that silently dropped every assigned customer who did not
convert. Since the discount roughly doubled the conversion rate, that mistake buried the real
effect and made a working campaign look like a failure. This was fixed by persisting the
customer-level assignment at generation time instead of inferring it from order history; see
`campaign_assignment` in `customers`.

### Step 5: Dashboard (`dashboard.html`)
A 6-section BI dashboard (Overview, Segments, Retention, Campaign Test, Category/Region, Channels)
built with Chart.js, mirroring what would be shipped in Power BI or Tableau, but as a portable,
dependency-free HTML file. Open it directly in any browser (keep `embedded_data.js` in the same
folder).

## 4. Key findings

**1. Revenue grew 102% year over year** (Rs. 18.9 Cr to Rs. 38.2 Cr), driven mostly by
festive-season order volume (October to November) and a growing Tier-1 customer base, but average
order value stayed flat. Growth is coming from more customers, not a higher basket size.

**2. RFM segmentation reveals a concentration risk.** The "Champions" segment is only about 16% of
customers but generates about 38% of total revenue. "Hibernating" customers (about 20% of the
base) generate almost nothing, making them a clearer win-back campaign target than continued
broad-based marketing spend.

**3. Retention decays fast and stabilizes around month 3.** After the first full month
post-signup, retention drops and flattens near 32% by month 6, meaning most churn risk is
front-loaded, and win-back interventions are most valuable in the first 60 to 90 days.

**4. The February 2025 discount campaign worked, and worked well.** On an intent-to-treat basis
(every assigned customer counted, not just the ones who bought something), treatment customers
generated 67.4% more revenue per assigned customer than control (Rs. 5,369 vs. Rs. 3,206),
confirmed by a Welch's t-test (p < 0.001). The effect is almost entirely a conversion story: 32.9%
of treatment customers purchased in the window vs. 13.8% of control (chi-square p < 0.001), so the
discount brought in incremental buyers rather than just subsidizing people who would have bought
anyway. Recommendation: scale the campaign beyond the pilot, and test whether a smaller discount
(for example, 10% flat instead of up to 20%) captures most of the conversion lift at better
margin.

**5. Referral and Organic Search customers have the highest revenue per customer** (approximately
Rs. 97,000 to 98,000) despite zero or near-zero acquisition cost, while Email is the least
efficient channel, a case for reallocating acquisition budget.

## 5. Files

```
01_generate_data.py       synthetic data generator with seasonality and campaign design
02_clean_and_load.py      ETL: dedup, fix nulls/typos, validate, load to SQLite
03_analysis_queries.sql   8 hand-written analytical SQL queries
04_analysis.py            runs the SQL layer, adds t-test/CI, exports dashboard JSON
raw_customers.csv         raw (messy) extract
raw_orders.csv            raw (messy) extract
datavista.db               cleaned SQLite warehouse
dashboard_data.json       analysis output
embedded_data.js          same data, inlined for the dashboard
dashboard.html            the BI dashboard, open in any browser
cleaning_log.txt          ETL audit log
```

## 6. Resume bullets (ready to use)

- Built an end-to-end analytics pipeline (SQL and Python) processing 30K+ transactions across
  6,000 customers, from raw data cleaning through RFM segmentation, cohort retention analysis, and
  a BI dashboard
- Wrote SQL window-function queries (NTILE, LAG, self-joins) to segment customers via RFM analysis
  and track month-over-month cohort retention, identifying that the top 16% of customers drove 38%
  of revenue
- Designed and statistically evaluated a marketing A/B test using an intent-to-treat framework,
  Welch's t-test, and a chi-square conversion test (all p < 0.001), quantifying a 67% revenue per
  customer uplift and recommending the campaign be scaled
- Built a 6-section interactive BI dashboard (Chart.js) translating SQL analysis into
  stakeholder-ready visuals covering revenue trends, customer segments, retention, and channel
  efficiency
- Diagnosed and corrected data quality issues (duplicate records, sign errors, missing values) in
  a raw transactional dataset as part of an ETL pipeline feeding a SQLite warehouse
