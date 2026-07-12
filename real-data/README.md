# DataVista: Real Data (Dunnhumby Complete Journey)

A validation pass of the DataVista pipeline against real, third-party retail data: 2,500
households, approximately 2.6 million real transaction line items, real marketing campaigns, over
a two-year period from an anonymized US grocery retailer, published by Dunnhumby.

This is not a rebuild from scratch. It is the same methodology proven on the synthetic project
(`../synthetic/`), re-applied to real data to test whether the approach holds up once control over
the data-generating process is lost.

## Why this exists

Synthetic data is useful for proving a pipeline can be built, but it cannot prove the ability to
handle real world data quality issues: missing demographics, non-random campaign targeting, and
ambiguous "did the customer churn, or was the customer simply not observed" signal. This project
exists to demonstrate that specific layer of analytical judgment.

## Data source

[Dunnhumby "The Complete Journey"](https://www.dunnhumby.com/source-files/): household-level
transaction data from 2,500 frequent shoppers at a real US grocery retailer, over roughly two
years, including real campaign and coupon data.

The source files are not included in this repository (approximately 800 MB). Download the dataset
from Kaggle and place the 8 CSV files in `real-data/raw/` before running the pipeline.

## Key differences from the synthetic version

| Synthetic project | Real data | Reason for the difference |
|---|---|---|
| Randomized 50/50 campaign split | Campaign 18 recipients, non-randomly targeted | Real retailers do not randomize; targeting is based on prior purchase behavior |
| `signup_date` per customer | No signup date exists | Proxy used: cohort defined as a household's first basket date (documented substitution) |
| 6 synthetic product categories | Real department/commodity hierarchy | Taken directly from `product.csv` |
| Acquisition channel field | Store-level performance | Real data has no channel field; `store_id` is the closest equivalent dimension |
| Injected nulls and duplicates | Genuine 68% missing demographic coverage | Reflects the source data's actual gaps; 1,699 of 2,500 households have no demographic record at all |

## Pipeline

| Step | Script | Purpose |
|---|---|---|
| 1 | `01_load_real_data.py` | Inspect raw CSVs, confirm schema and row counts |
| 2 | `02_clean_and_load.py` | Build a 3-table warehouse: `customers`, `baskets` (order-level), `basket_items` (line-item detail) |
| 3 | `03_inspect_campaigns.py` | Exploratory comparison of all 30 campaigns by recipient count and redemption rate, to select a candidate for analysis |
| 4 | `04_campaign_balance_check.py` | Checks whether Campaign 18 recipients and non-recipients are demographically comparable, since assignment is not randomized |
| 5 | `05_campaign_analysis.py` | Intent-to-treat revenue comparison on Campaign 18: Welch's t-test and a chi-square test on conversion |
| 6 | `06_analysis.py` | RFM segmentation, cohort retention, category and store performance; exports `dashboard_data_real.json` |
| 7 | `07_analysis_queries_real.sql` | The same analyses expressed as hand-written SQL |
| 8 | `make_embedded_real.py` | Packages the JSON output for the dashboard |
| n/a | `dashboard.html` | The same 6-section Chart.js dashboard, adapted for real data |

## Key findings

**1. Demographic data covers only 32% of households** (801 of 2,500). This is a real, structural
gap in the source data, not injected messiness. Any demographic-cut analysis (income, household
size) should be read as a sample of the customer base, not the full population.

**2. Campaign 18 recipients spent more during the campaign window.** Unlike the synthetic
campaign test, recipients were not randomly assigned. A balance check on income, age, household
size, and homeowner status showed the two groups are broadly comparable, with one notable gap:
large households are underrepresented among recipients. This finding is reported as associational,
not causal.

*Uplift percentage, p-value, and conversion rates to be added from `campaign_summary.json` once
the campaign analysis phase is finalized.*

**3. RFM segmentation and cohort retention findings to be added** once the corresponding analysis
phase is finalized, in the same format as the synthetic project's README.

## Honest limitations

- Cohort "signup" is a proxy (first basket date), not a true acquisition date. A household could
  have shopped elsewhere before this dataset's observation window begins.
- Campaign 18 is one of 30 available campaigns, selected for sample size and redemption rate, not
  necessarily because it is the most informative campaign in the dataset.
- Campaign assignment is non-random, so the campaign result is associational rather than causal.
- `causal_data.csv` (in-store display and mailer data) was not used in this pass. It is a natural
  next extension of the analysis.

## Files

```
real-data/
├── raw/                          source CSVs from Kaggle, not included, approximately 800MB
├── 01_load_real_data.py
├── 02_clean_and_load.py
├── 03_inspect_campaigns.py
├── 04_campaign_balance_check.py
├── 05_campaign_analysis.py
├── 06_analysis.py
├── 07_analysis_queries_real.sql
├── make_embedded_real.py
├── dashboard_data_real.json
├── embedded_data_real.js
├── dashboard.html
└── README.md
```
