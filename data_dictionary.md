# Data Dictionary - Bluestock Mutual Fund Analytics

This document describes the schema of the `bluestock_mf.db` SQLite database. The schema follows a **star schema** pattern optimized for mutual fund data analysis.

---

## 1. Dimension Tables

### Table: `dim_fund`
Stores metadata and details for each mutual fund scheme.
* **Source Reference**: `data/processed/01_fund_master.csv`
* **Primary Key**: `amfi_code`

| Column Name | SQLite Data Type | Constraints | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PRIMARY KEY | Unique numeric code assigned to each mutual fund scheme by AMFI (Association of Mutual Funds in India). |
| `fund_house` | TEXT | NOT NULL | Asset Management Company (AMC) name managing the fund (e.g. "SBI Mutual Fund"). |
| `scheme_name` | TEXT | NOT NULL | Name of the mutual fund scheme including plan and option (e.g. "SBI Bluechip Fund - Regular Plan - Growth"). |
| `category` | TEXT | NOT NULL | Asset class division (e.g. "Equity", "Debt"). |
| `sub_category` | TEXT | NOT NULL | Specific investment mandate division (e.g. "Large Cap", "Small Cap", "Liquid"). |
| `plan` | TEXT | NOT NULL, CHECK | Direct vs Regular Plan options (`CHECK(plan IN ('Direct', 'Regular'))`). |
| `launch_date` | TEXT | - | Date when the mutual fund scheme was launched in `YYYY-MM-DD` format. |
| `benchmark` | TEXT | - | Benchmark index against which the fund's returns are evaluated (e.g. "NIFTY 100 TRI"). |
| `expense_ratio_pct`| REAL | CHECK | The annual fee charged by the fund, expressed as a percentage of AUM (`>= 0.0`). |
| `exit_load_pct` | REAL | CHECK | Penalty fee charged to investors who redeem shares before a specified period (`>= 0.0`). |
| `min_sip_amount` | INTEGER | CHECK | Minimum allowed transaction size for Systematic Investment Plan (`>= 0`). |
| `min_lumpsum_amount`| INTEGER | CHECK | Minimum allowed initial one-time investment size (`>= 0`). |
| `fund_manager` | TEXT | - | Name of the primary fund manager overseeing the portfolio. |
| `risk_category` | TEXT | NOT NULL | Risk level classification (e.g. "Low", "Moderate", "Very High"). |
| `sebi_category_code`| TEXT | - | SEBI-standardized category code (e.g., "EC01" for Equity Large Cap). |

---

### Table: `dim_date`
Calendar dimension table spanning `2022-01-01` to `2026-12-31`. Contains pre-computed date components to simplify temporal queries (e.g., weekends, quarters).
* **Source Reference**: Generated programmatically in `db_loader.py`
* **Primary Key**: `date`

| Column Name | SQLite Data Type | Constraints | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `date` | TEXT | PRIMARY KEY | Calendar date in `YYYY-MM-DD` format. |
| `year` | INTEGER | NOT NULL | Calendar year (e.g. 2024). |
| `month` | INTEGER | NOT NULL, CHECK | Numeric calendar month of the year (`BETWEEN 1 AND 12`). |
| `day` | INTEGER | NOT NULL, CHECK | Day of the month (`BETWEEN 1 AND 31`). |
| `quarter` | INTEGER | NOT NULL, CHECK | Calendar quarter of the year (`BETWEEN 1 AND 4`). |
| `is_weekend` | INTEGER | NOT NULL, CHECK | Binary flag identifying if the date falls on a Saturday or Sunday (`IN (0, 1)`). |
| `month_name` | TEXT | NOT NULL | Complete month name (e.g. "January"). |
| `day_name` | TEXT | NOT NULL | Complete weekday name (e.g. "Monday"). |

---

## 2. Fact Tables

### Table: `fact_nav`
Daily Net Asset Value (NAV) history records.
* **Source Reference**: `data/processed/02_nav_history.csv`
* **Primary Key**: `nav_id`

| Column Name | SQLite Data Type | Constraints | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `nav_id` | INTEGER | PRIMARY KEY | Auto-incrementing identifier. |
| `amfi_code` | INTEGER | FOREIGN KEY | Identifies the mutual fund scheme. References `dim_fund(amfi_code)`. |
| `date` | TEXT | FOREIGN KEY | Identifies the calendar date. References `dim_date(date)`. |
| `nav` | REAL | NOT NULL, CHECK | Net Asset Value (NAV) price per share of the fund on that date (`> 0`). |
| `is_holiday_weekend_filled` | INTEGER | NOT NULL, CHECK | Binary flag identifying if the NAV was forward-filled from the previous business day (`IN (0, 1)`). |

---

### Table: `fact_transactions`
Individual investor transaction records.
* **Source Reference**: `data/processed/08_investor_transactions.csv`
* **Primary Key**: `transaction_id`

| Column Name | SQLite Data Type | Constraints | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `transaction_id` | INTEGER | PRIMARY KEY | Auto-incrementing identifier. |
| `investor_id` | TEXT | NOT NULL | Unique identifier for the individual investor. |
| `transaction_date`| TEXT | FOREIGN KEY | Date the transaction took place. References `dim_date(date)`. |
| `amfi_code` | INTEGER | FOREIGN KEY | Identifies the mutual fund scheme. References `dim_fund(amfi_code)`. |
| `transaction_type`| TEXT | NOT NULL, CHECK | Type of transaction (`CHECK IN ('SIP', 'Lumpsum', 'Redemption')`). |
| `amount_inr` | REAL | NOT NULL, CHECK | Monetary size of the transaction in Indian Rupees (`> 0`). |
| `state` | TEXT | NOT NULL | Indian state of the investor's residence. |
| `city` | TEXT | NOT NULL | City of the investor's residence. |
| `city_tier` | TEXT | - | Classification tier of the city (e.g., "T30" or "B30"). |
| `age_group` | TEXT | - | Categorical age segment of the investor (e.g., "18-25", "36-45"). |
| `gender` | TEXT | - | Investor's gender ("Male", "Female"). |
| `annual_income_lakh`| REAL | - | Investor's annual income, represented in Lakhs of INR. |
| `payment_mode` | TEXT | - | Method used for the transaction (e.g. "UPI", "Cheque", "Net Banking"). |
| `kyc_status` | TEXT | CHECK | KYC status check of the investor (`CHECK IN ('Verified', 'Pending')`). |

---

### Table: `fact_performance`
Return and risk metric summary table for each mutual fund scheme.
* **Source Reference**: `data/processed/07_scheme_performance.csv`
* **Primary Key**: `amfi_code`

| Column Name | SQLite Data Type | Constraints | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PRIMARY KEY, FK | Identifies the scheme. References `dim_fund(amfi_code)`. |
| `return_1yr_pct` | REAL | - | 1-Year historical annual return percentage. |
| `return_3yr_pct` | REAL | - | 3-Year historical annualized return percentage. |
| `return_5yr_pct` | REAL | - | 5-Year historical annualized return percentage. |
| `benchmark_3yr_pct`| REAL | - | 3-Year historical benchmark return percentage. |
| `alpha` | REAL | - | Risk-adjusted outperformance metric relative to the benchmark. |
| `beta` | REAL | - | Sensitivity measure of the fund's returns relative to benchmark fluctuations. |
| `sharpe_ratio` | REAL | - | Performance measure representing returns generated per unit of risk. |
| `sortino_ratio` | REAL | - | Risk-adjusted return measure focusing only on downside volatility. |
| `std_dev_ann_pct` | REAL | - | Annualized standard deviation of returns (volatility measure). |
| `max_drawdown_pct` | REAL | - | Peak-to-trough decline percentage representing maximum historical paper loss. |
| `aum_crore` | INTEGER | - | Total assets under management of the fund, represented in Crores. |
| `expense_ratio_pct`| REAL | - | Standardized expense ratio metric. |
| `morningstar_rating`| INTEGER | CHECK | Rating stars representing quality scores (`BETWEEN 1 AND 5`). |
| `risk_grade` | TEXT | - | Qualitatively annotated risk grade (e.g. "Moderate", "Very High"). |
| `is_expense_ratio_anomalous` | INTEGER | CHECK | Flag indicating if the expense ratio is out of the standard `[0.1%, 2.5%]` interval. |

---

### Table: `fact_aum`
Historical Assets Under Management (AUM) snapshots for each fund house.
* **Source Reference**: `data/processed/03_aum_by_fund_house.csv`
* **Primary Key**: `aum_id`

| Column Name | SQLite Data Type | Constraints | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `aum_id` | INTEGER | PRIMARY KEY | Auto-incrementing identifier. |
| `date` | TEXT | FOREIGN KEY | Date of the AUM snapshot. References `dim_date(date)`. |
| `fund_house` | TEXT | NOT NULL | Asset Management Company name. |
| `aum_lakh_crore` | REAL | CHECK | Inflow size represented in Lakh Crores of INR (`>= 0`). |
| `aum_crore` | INTEGER | CHECK | Inflow size represented in Crores of INR (`>= 0`). |
| `num_schemes` | INTEGER | CHECK | Number of active schemes managed by the AMC on that date (`>= 0`). |

---

## 3. Supplementary Fact Tables

### Table: `fact_holdings`
Stock holdings of each fund's portfolio.
* **Source Reference**: `data/processed/09_portfolio_holdings.csv`
* **Primary Key**: `holding_id`

| Column Name | SQLite Data Type | Constraints | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `holding_id` | INTEGER | PRIMARY KEY | Auto-incrementing identifier. |
| `amfi_code` | INTEGER | FOREIGN KEY | Identifies the mutual fund scheme. References `dim_fund(amfi_code)`. |
| `stock_symbol` | TEXT | NOT NULL | Stock exchange trading ticker symbol (e.g., "HDFCBANK"). |
| `stock_name` | TEXT | NOT NULL | Official company name. |
| `sector` | TEXT | NOT NULL | Economic sector classification (e.g., "Financial Services"). |
| `weight_pct` | REAL | NOT NULL, CHECK | Allocation weight of this stock within the fund's portfolio (`BETWEEN 0 AND 100`). |
| `market_value_cr` | REAL | - | Market value of the holding in Crores of INR. |
| `current_price_inr`| REAL | - | Market price of one share of the stock in INR. |
| `portfolio_date` | TEXT | FOREIGN KEY | Snapshot reporting date. References `dim_date(date)`. |

---

### Table: `fact_benchmark`
Daily closing values of benchmark indices.
* **Source Reference**: `data/processed/10_benchmark_indices.csv`
* **Primary Key**: `benchmark_id`

| Column Name | SQLite Data Type | Constraints | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `benchmark_id` | INTEGER | PRIMARY KEY | Auto-incrementing identifier. |
| `date` | TEXT | FOREIGN KEY | Calendar date. References `dim_date(date)`. |
| `index_name` | TEXT | NOT NULL | Name of the benchmark index (e.g. "NIFTY50"). |
| `close_value` | REAL | NOT NULL, CHECK | Index closing value price (`>= 0`). |

---

### Table: `fact_sip_inflows`
Industry-wide monthly SIP inflow snapshots.
* **Source Reference**: `data/processed/04_monthly_sip_inflows.csv`
* **Primary Key**: `sip_inflow_id`

| Column Name | SQLite Data Type | Constraints | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `sip_inflow_id` | INTEGER | PRIMARY KEY | Auto-incrementing identifier. |
| `month` | TEXT | NOT NULL | Month in `YYYY-MM` format. |
| `sip_inflow_crore` | INTEGER | CHECK | Aggregate SIP monthly inflows in Crores (`>= 0`). |
| `active_sip_accounts_crore`| REAL | CHECK | Count of active SIP accounts in Crores (`>= 0`). |
| `new_sip_accounts_lakh`| REAL | CHECK | Number of new SIP accounts registered in the month, in Lakhs (`>= 0`). |
| `sip_aum_lakh_crore`| REAL | CHECK | Total SIP assets under management in Lakh Crores (`>= 0`). |
| `yoy_growth_pct` | REAL | - | Year-Over-Year percentage growth. |

---

### Table: `fact_category_inflows`
Industry-wide monthly net inflows per category.
* **Source Reference**: `data/processed/05_category_inflows.csv`
* **Primary Key**: `category_inflow_id`

| Column Name | SQLite Data Type | Constraints | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `category_inflow_id`| INTEGER | PRIMARY KEY | Auto-incrementing identifier. |
| `month` | TEXT | NOT NULL | Month in `YYYY-MM` format. |
| `category` | TEXT | NOT NULL | Specific category division (e.g. "Large Cap"). |
| `net_inflow_crore` | REAL | - | Total net inflow or outflow in Crores of INR (can be negative). |

---

### Table: `fact_folio_count`
Industry-wide monthly active folio counts by asset class.
* **Source Reference**: `data/processed/06_industry_folio_count.csv`
* **Primary Key**: `folio_count_id`

| Column Name | SQLite Data Type | Constraints | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `folio_count_id` | INTEGER | PRIMARY KEY | Auto-incrementing identifier. |
| `month` | TEXT | NOT NULL | Month in `YYYY-MM` format. |
| `total_folios_crore`| REAL | CHECK | Total mutual fund active folios in Crores (`>= 0`). |
| `equity_folios_crore`| REAL | CHECK | Total equity asset active folios in Crores (`>= 0`). |
| `debt_folios_crore` | REAL | CHECK | Total debt asset active folios in Crores (`>= 0`). |
| `hybrid_folios_crore`| REAL | CHECK | Total hybrid asset active folios in Crores (`>= 0`). |
| `others_folios_crore`| REAL | CHECK | Total other asset (ETF, Gold etc.) active folios in Crores (`>= 0`). |
