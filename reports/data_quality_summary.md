# Data Quality & Ingestion Summary - Day 1

This report provides an automated data quality summary for the loaded Mutual Fund datasets.

## 1. Datasets Ingested

| File Name | Display Name | Rows | Columns | Status |
| --- | --- | --- | --- | --- |
| 01_fund_master.csv | Fund Master | 40 | 15 | ✅ Clean |
| 02_nav_history.csv | NAV History | 46,000 | 3 | ✅ Clean |
| 03_aum_by_fund_house.csv | AUM by Fund House | 90 | 5 | ✅ Clean |
| 04_monthly_sip_inflows.csv | Monthly SIP Inflows | 48 | 6 | ⚠️ Anomalies Detected |
| 05_category_inflows.csv | Category Inflows | 144 | 3 | ✅ Clean |
| 06_industry_folio_count.csv | Industry Folio Count | 21 | 6 | ✅ Clean |
| 07_scheme_performance.csv | Scheme Performance | 40 | 19 | ⚠️ Anomalies Detected |
| 08_investor_transactions.csv | Investor Transactions | 32,778 | 13 | ✅ Clean |
| 09_portfolio_holdings.csv | Portfolio Holdings | 322 | 8 | ✅ Clean |
| 10_benchmark_indices.csv | Benchmark Indices | 8,050 | 3 | ✅ Clean |

## 2. In-Depth Dataset Anomalies

### Monthly SIP Inflows (`04_monthly_sip_inflows.csv`)
- Missing Values: Column 'yoy_growth_pct' has 12 nulls (25.00%)

### Scheme Performance (`07_scheme_performance.csv`)
- Negative Values: Column 'max_drawdown_pct' contains negative values (Min: -33.5)

## 3. Fund Master Dimensions

- **Unique Fund Houses (10):** SBI Mutual Fund, HDFC Mutual Fund, ICICI Prudential MF, Nippon India MF, Kotak Mahindra MF, Axis Mutual Fund, Aditya Birla Sun Life MF, UTI Mutual Fund, Mirae Asset MF, DSP Mutual Fund
- **Unique Categories (2):** Equity, Debt
- **Unique Sub-Categories (12):** Large Cap, Small Cap, Gilt, Mid Cap, Short Duration, Value, Liquid, Index/ETF, Flexi Cap, Index, Large & Mid Cap, ELSS
- **Unique Risk Categories (5):** Moderate, Very High, Low, High, Moderately High

## 4. AMFI Code Validation Results

- **Unique Codes in Fund Master:** 40
- **Unique Codes in NAV History:** 40
- **Matching Codes:** 40 / 40 (100.00%)

✅ **Data Integrity Check Passed:** All codes defined in the Fund Master are successfully mapped in the NAV History.
