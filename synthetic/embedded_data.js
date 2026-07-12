const DATA = {
  "kpi_by_year": [
    {
      "order_year": "2024",
      "total_orders": 10414,
      "active_customers": 2644,
      "net_revenue": 188735639.77,
      "avg_order_value": 18123.26
    },
    {
      "order_year": "2025",
      "total_orders": 21304,
      "active_customers": 4505,
      "net_revenue": 381539215.55,
      "avg_order_value": 17909.28
    }
  ],
  "monthly_revenue": [
    {
      "ym": "2024-01",
      "revenue": 1061338.94
    },
    {
      "ym": "2024-02",
      "revenue": 4096742.82
    },
    {
      "ym": "2024-03",
      "revenue": 5656889.27
    },
    {
      "ym": "2024-04",
      "revenue": 8268015.03
    },
    {
      "ym": "2024-05",
      "revenue": 9904045.82
    },
    {
      "ym": "2024-06",
      "revenue": 11376536.78
    },
    {
      "ym": "2024-07",
      "revenue": 9696637.71
    },
    {
      "ym": "2024-08",
      "revenue": 9712963.16
    },
    {
      "ym": "2024-09",
      "revenue": 15848901.05
    },
    {
      "ym": "2024-10",
      "revenue": 38295243.8
    },
    {
      "ym": "2024-11",
      "revenue": 44139057.56
    },
    {
      "ym": "2024-12",
      "revenue": 30679267.83
    },
    {
      "ym": "2025-01",
      "revenue": 26069483.28
    },
    {
      "ym": "2025-02",
      "revenue": 26810723.28
    },
    {
      "ym": "2025-03",
      "revenue": 21554331.12
    },
    {
      "ym": "2025-04",
      "revenue": 24029958.95
    },
    {
      "ym": "2025-05",
      "revenue": 23716526.13
    },
    {
      "ym": "2025-06",
      "revenue": 24924306.64
    },
    {
      "ym": "2025-07",
      "revenue": 18211055.88
    },
    {
      "ym": "2025-08",
      "revenue": 18586144.96
    },
    {
      "ym": "2025-09",
      "revenue": 24834341.25
    },
    {
      "ym": "2025-10",
      "revenue": 65095320.41
    },
    {
      "ym": "2025-11",
      "revenue": 65031475.43
    },
    {
      "ym": "2025-12",
      "revenue": 42675548.22
    }
  ],
  "rfm_rollup": [
    {
      "rfm_segment": "Champions",
      "customers": 982,
      "avg_ltv": 221056.0,
      "segment_revenue": 217076547.0
    },
    {
      "rfm_segment": "Needs Attention",
      "customers": 1493,
      "avg_ltv": 100344.0,
      "segment_revenue": 149813598.0
    },
    {
      "rfm_segment": "At Risk (high value)",
      "customers": 577,
      "avg_ltv": 161085.0,
      "segment_revenue": 92946249.0
    },
    {
      "rfm_segment": "Loyal Customers",
      "customers": 628,
      "avg_ltv": 82685.0,
      "segment_revenue": 51926327.0
    },
    {
      "rfm_segment": "Hibernating",
      "customers": 1175,
      "avg_ltv": 31716.0,
      "segment_revenue": 37266666.0
    },
    {
      "rfm_segment": "New / Promising",
      "customers": 552,
      "avg_ltv": 38488.0,
      "segment_revenue": 21245468.0
    }
  ],
  "avg_retention_curve": [
    {
      "month_index": 0,
      "retention_pct": 27.7
    },
    {
      "month_index": 1,
      "retention_pct": 54.0
    },
    {
      "month_index": 2,
      "retention_pct": 38.9
    },
    {
      "month_index": 3,
      "retention_pct": 36.7
    },
    {
      "month_index": 4,
      "retention_pct": 34.8
    },
    {
      "month_index": 5,
      "retention_pct": 33.5
    },
    {
      "month_index": 6,
      "retention_pct": 31.7
    }
  ],
  "campaign_ab_test": {
    "treatment_customers": 1761,
    "control_customers": 1762,
    "treatment_avg_revenue": 5368.71,
    "control_avg_revenue": 3206.24,
    "treatment_ci_95": [
      4748.73,
      5988.7
    ],
    "control_ci_95": [
      2601.49,
      3810.99
    ],
    "uplift_pct": 67.4,
    "t_statistic": 4.894,
    "p_value": 0.0,
    "significant_at_95": true,
    "treatment_conversion_rate_pct": 32.9,
    "control_conversion_rate_pct": 13.8,
    "conversion_chi2": 179.24,
    "conversion_p_value": 0.0
  },
  "category_region": [
    {
      "region_tier": "Tier 1",
      "product_category": "Mobiles & Accessories",
      "orders": 3949,
      "revenue": 110668422.73,
      "avg_order_value": 28024.42,
      "return_rate_pct": 5.17
    },
    {
      "region_tier": "Tier 1",
      "product_category": "Electronics",
      "orders": 2102,
      "revenue": 78284806.18,
      "avg_order_value": 37243.01,
      "return_rate_pct": 3.9
    },
    {
      "region_tier": "Tier 1",
      "product_category": "Home Appliances",
      "orders": 2293,
      "revenue": 54422212.19,
      "avg_order_value": 23734.07,
      "return_rate_pct": 5.19
    },
    {
      "region_tier": "Tier 1",
      "product_category": "Home & Kitchen",
      "orders": 1666,
      "revenue": 12604659.17,
      "avg_order_value": 7565.82,
      "return_rate_pct": 4.14
    },
    {
      "region_tier": "Tier 1",
      "product_category": "Fashion",
      "orders": 3095,
      "revenue": 9325291.45,
      "avg_order_value": 3013.02,
      "return_rate_pct": 10.89
    },
    {
      "region_tier": "Tier 1",
      "product_category": "Beauty & Personal Care",
      "orders": 2142,
      "revenue": 4846301.95,
      "avg_order_value": 2262.51,
      "return_rate_pct": 4.48
    },
    {
      "region_tier": "Tier 2",
      "product_category": "Mobiles & Accessories",
      "orders": 3275,
      "revenue": 93315853.58,
      "avg_order_value": 28493.39,
      "return_rate_pct": 4.34
    },
    {
      "region_tier": "Tier 2",
      "product_category": "Electronics",
      "orders": 1839,
      "revenue": 70084019.38,
      "avg_order_value": 38109.85,
      "return_rate_pct": 3.64
    },
    {
      "region_tier": "Tier 2",
      "product_category": "Home Appliances",
      "orders": 1869,
      "revenue": 44794993.65,
      "avg_order_value": 23967.36,
      "return_rate_pct": 4.71
    },
    {
      "region_tier": "Tier 2",
      "product_category": "Home & Kitchen",
      "orders": 1415,
      "revenue": 10216725.28,
      "avg_order_value": 7220.3,
      "return_rate_pct": 4.73
    },
    {
      "region_tier": "Tier 2",
      "product_category": "Fashion",
      "orders": 2593,
      "revenue": 7683212.86,
      "avg_order_value": 2963.06,
      "return_rate_pct": 11.07
    },
    {
      "region_tier": "Tier 2",
      "product_category": "Beauty & Personal Care",
      "orders": 1789,
      "revenue": 3977947.08,
      "avg_order_value": 2223.56,
      "return_rate_pct": 5.2
    },
    {
      "region_tier": "Tier 3",
      "product_category": "Mobiles & Accessories",
      "orders": 1432,
      "revenue": 39997419.56,
      "avg_order_value": 27931.16,
      "return_rate_pct": 4.82
    },
    {
      "region_tier": "Tier 3",
      "product_category": "Electronics",
      "orders": 807,
      "revenue": 28943366.69,
      "avg_order_value": 35865.39,
      "return_rate_pct": 4.71
    },
    {
      "region_tier": "Tier 3",
      "product_category": "Home Appliances",
      "orders": 806,
      "revenue": 19668936.03,
      "avg_order_value": 24403.15,
      "return_rate_pct": 4.22
    },
    {
      "region_tier": "Tier 3",
      "product_category": "Home & Kitchen",
      "orders": 582,
      "revenue": 4274370.57,
      "avg_order_value": 7344.28,
      "return_rate_pct": 2.06
    },
    {
      "region_tier": "Tier 3",
      "product_category": "Fashion",
      "orders": 1162,
      "revenue": 3502535.83,
      "avg_order_value": 3014.23,
      "return_rate_pct": 10.24
    },
    {
      "region_tier": "Tier 3",
      "product_category": "Beauty & Personal Care",
      "orders": 854,
      "revenue": 1959457.97,
      "avg_order_value": 2294.45,
      "return_rate_pct": 3.4
    }
  ],
  "channel_performance": [
    {
      "acquisition_channel": "Referral",
      "customers_acquired": 770,
      "total_revenue": 75321850.08,
      "revenue_per_customer": 97820.58
    },
    {
      "acquisition_channel": "Organic Search",
      "customers_acquired": 1950,
      "total_revenue": 187462912.0,
      "revenue_per_customer": 96134.83
    },
    {
      "acquisition_channel": "Direct",
      "customers_acquired": 856,
      "total_revenue": 81693962.43,
      "revenue_per_customer": 95436.87
    },
    {
      "acquisition_channel": "Paid Social",
      "customers_acquired": 1689,
      "total_revenue": 160885316.48,
      "revenue_per_customer": 95254.78
    },
    {
      "acquisition_channel": "Email",
      "customers_acquired": 735,
      "total_revenue": 64910814.33,
      "revenue_per_customer": 88314.03
    }
  ],
  "category_total": [
    {
      "product_category": "Mobiles & Accessories",
      "revenue": 232278151.68,
      "orders": 8241
    },
    {
      "product_category": "Electronics",
      "revenue": 170096214.18,
      "orders": 4561
    },
    {
      "product_category": "Home Appliances",
      "revenue": 113325591.27,
      "orders": 4727
    },
    {
      "product_category": "Home & Kitchen",
      "revenue": 25943260.3,
      "orders": 3515
    },
    {
      "product_category": "Fashion",
      "revenue": 18352885.07,
      "orders": 6107
    },
    {
      "product_category": "Beauty & Personal Care",
      "revenue": 10278752.82,
      "orders": 4567
    }
  ],
  "totals": {
    "total_customers": 6000,
    "total_orders": 31718,
    "total_revenue": 570274855.32,
    "return_rate_pct": 5.8
  }
};
