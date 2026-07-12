# DataVista: End-to-end Pipeline

An end-to-end retail analytics case study, built in two parts: first on synthetic data to prove
the pipeline works end to end, then re-applied to a real, third-party dataset to test whether the
approach holds up once control over the data-generating process is lost.

Both parts follow the same methodology:

```
raw data -> ETL/cleaning -> SQL warehouse -> SQL analysis -> statistical testing -> dashboard -> business recommendations
```

## Repository structure

| Folder | Description |
|---|---|
| [`synthetic/`](synthetic/) | The full pipeline, built and stress-tested first, on a synthetic simulated e-commerce dataset (6,000 customers, approximately 33,670 orders) |
| [`real-data/`](real-data/) | The same methodology applied to a real, third-party grocery dataset (2,500 households, approximately 2.6 million transaction line items) |

## Why two implementations

Synthetic data is useful for proving a pipeline can be built end to end, under conditions the
author controls. It cannot prove the same approach holds up against real world data: missing
demographic coverage, non-random campaign targeting, and ambiguous signals that a purely
synthetic dataset will not contain. This project was built in two stages specifically to
demonstrate both capabilities: build the pipeline, then prove it against data the author did not
generate.

## synthetic/: the pipeline, built and stress-tested first

A simulated mid-size Indian e-commerce retailer, generated with deliberate messiness (duplicates,
null values, inconsistent casing, a pricing sign-error bug) and a genuine randomized marketing
campaign. Includes RFM segmentation, cohort retention, an intent-to-treat A/B test using Welch's
t-test and a chi-square test, and a Chart.js dashboard.

The synthetic project also includes a documented case of catching and correcting a real
statistical error: a post-treatment selection bug in an earlier version of the campaign analysis
that silently dropped every assigned customer who did not convert, which buried a genuine campaign
effect. See `synthetic/README.md` for the full writeup.

## real-data/: the same methodology, applied to real data

The Dunnhumby "Complete Journey" dataset: 2,500 real households, roughly 2.6 million real
transaction line items, and real, non-randomized marketing campaigns from an anonymized US grocery
retailer, spanning approximately two years.

This half of the project exists specifically to demonstrate the layer synthetic data cannot teach:

| Area | Synthetic project | Real data | Reason for the difference |
|---|---|---|---|
| Campaign assignment | Randomized 50/50 split | Non-random targeting (Campaign 18) | Real retailers target campaigns based on prior purchase behavior, not randomization |
| Customer tenure | `signup_date` field per customer | No signup date exists | Proxy used: cohort defined as a household's first basket date (documented substitution) |
| Product taxonomy | 6 synthetic categories | Real department/commodity hierarchy | Taken directly from the source `product.csv` |
| Acquisition | Acquisition channel field | Store-level performance | Real data has no channel field; `store_id` is the closest equivalent dimension |
| Data quality | Injected nulls and duplicates | Genuine 68% missing demographic coverage | Reflects the real data's actual gaps, not simulated messiness |

Because campaign assignment in the real data is not randomized, the campaign analysis in
`real-data/` is reported as associational rather than causal, following a documented balance check
between recipients and non-recipients. See `real-data/README.md` for full findings, pipeline
detail, and limitations.

## Data note

The real-data project requires the Dunnhumby "The Complete Journey" source files, which are not
included in this repository due to size (approximately 800 MB). See `real-data/README.md` for
download and setup instructions.
