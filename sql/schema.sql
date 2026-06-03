-- schema.sql
-- SQLite Database Schema Definition for Mutual Fund Analytics

-- Enable Foreign Key support in SQLite (Note: must be run on connection establishment)
PRAGMA foreign_keys = ON;

-- Drop tables if they exist to start fresh
DROP TABLE IF EXISTS fact_holdings;
DROP TABLE IF EXISTS fact_benchmark;
DROP TABLE IF EXISTS fact_sip_inflows;
DROP TABLE IF EXISTS fact_category_inflows;
DROP TABLE IF EXISTS fact_folio_count;
DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_performance;
DROP TABLE IF EXISTS fact_nav;
DROP TABLE IF EXISTS fact_aum;
DROP TABLE IF EXISTS dim_fund;
DROP TABLE IF EXISTS dim_date;

-- 1. dim_fund Table (derived from 01_fund_master.csv)
CREATE TABLE dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    plan TEXT NOT NULL CHECK(plan IN ('Regular', 'Direct')),
    launch_date TEXT,
    benchmark TEXT,
    expense_ratio_pct REAL CHECK(expense_ratio_pct >= 0.0),
    exit_load_pct REAL CHECK(exit_load_pct >= 0.0),
    min_sip_amount INTEGER CHECK(min_sip_amount >= 0),
    min_lumpsum_amount INTEGER CHECK(min_lumpsum_amount >= 0),
    fund_manager TEXT,
    risk_category TEXT NOT NULL,
    sebi_category_code TEXT
);

-- 2. dim_date Table (generated calendar dimension)
CREATE TABLE dim_date (
    date TEXT PRIMARY KEY, -- 'YYYY-MM-DD'
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
    day INTEGER NOT NULL CHECK(day BETWEEN 1 AND 31),
    quarter INTEGER NOT NULL CHECK(quarter BETWEEN 1 AND 4),
    is_weekend INTEGER NOT NULL CHECK(is_weekend IN (0, 1)),
    month_name TEXT NOT NULL,
    day_name TEXT NOT NULL
);

-- 3. fact_nav Table (derived from 02_nav_history.csv)
CREATE TABLE fact_nav (
    nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    date TEXT NOT NULL,
    nav REAL NOT NULL CHECK(nav > 0),
    is_holiday_weekend_filled INTEGER NOT NULL CHECK(is_holiday_weekend_filled IN (0, 1)),
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE,
    FOREIGN KEY(date) REFERENCES dim_date(date) ON DELETE CASCADE,
    UNIQUE(amfi_code, date)
);

-- 4. fact_aum Table (derived from 03_aum_by_fund_house.csv)
CREATE TABLE fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    aum_lakh_crore REAL CHECK(aum_lakh_crore >= 0),
    aum_crore INTEGER CHECK(aum_crore >= 0),
    num_schemes INTEGER CHECK(num_schemes >= 0),
    FOREIGN KEY(date) REFERENCES dim_date(date) ON DELETE CASCADE
);

-- 5. fact_transactions Table (derived from 08_investor_transactions.csv)
CREATE TABLE fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    amfi_code INTEGER NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr REAL NOT NULL CHECK(amount_inr > 0),
    state TEXT NOT NULL,
    city TEXT NOT NULL,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT CHECK(kyc_status IN ('Verified', 'Pending')),
    FOREIGN KEY(transaction_date) REFERENCES dim_date(date) ON DELETE CASCADE,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE
);

-- 6. fact_performance Table (derived from 07_scheme_performance.csv)
CREATE TABLE fact_performance (
    amfi_code INTEGER PRIMARY KEY,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore INTEGER,
    expense_ratio_pct REAL,
    morningstar_rating INTEGER CHECK(morningstar_rating BETWEEN 1 AND 5),
    risk_grade TEXT,
    is_expense_ratio_anomalous INTEGER CHECK(is_expense_ratio_anomalous IN (0, 1)),
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE
);

-- 7. fact_holdings Table (derived from 09_portfolio_holdings.csv)
CREATE TABLE fact_holdings (
    holding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    stock_symbol TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    sector TEXT NOT NULL,
    weight_pct REAL NOT NULL CHECK(weight_pct BETWEEN 0 AND 100),
    market_value_cr REAL,
    current_price_inr REAL,
    portfolio_date TEXT NOT NULL,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE,
    FOREIGN KEY(portfolio_date) REFERENCES dim_date(date) ON DELETE CASCADE
);

-- 8. fact_benchmark Table (derived from 10_benchmark_indices.csv)
CREATE TABLE fact_benchmark (
    benchmark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    index_name TEXT NOT NULL,
    close_value REAL NOT NULL CHECK(close_value >= 0),
    FOREIGN KEY(date) REFERENCES dim_date(date) ON DELETE CASCADE
);

-- 9. fact_sip_inflows Table (derived from 04_monthly_sip_inflows.csv)
CREATE TABLE fact_sip_inflows (
    sip_inflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL, -- 'YYYY-MM'
    sip_inflow_crore INTEGER CHECK(sip_inflow_crore >= 0),
    active_sip_accounts_crore REAL CHECK(active_sip_accounts_crore >= 0),
    new_sip_accounts_lakh REAL CHECK(new_sip_accounts_lakh >= 0),
    sip_aum_lakh_crore REAL CHECK(sip_aum_lakh_crore >= 0),
    yoy_growth_pct REAL
);

-- 10. fact_category_inflows Table (derived from 05_category_inflows.csv)
CREATE TABLE fact_category_inflows (
    category_inflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL, -- 'YYYY-MM'
    category TEXT NOT NULL,
    net_inflow_crore REAL
);

-- 11. fact_folio_count Table (derived from 06_industry_folio_count.csv)
CREATE TABLE fact_folio_count (
    folio_count_id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL, -- 'YYYY-MM'
    total_folios_crore REAL CHECK(total_folios_crore >= 0),
    equity_folios_crore REAL CHECK(equity_folios_crore >= 0),
    debt_folios_crore REAL CHECK(debt_folios_crore >= 0),
    hybrid_folios_crore REAL CHECK(hybrid_folios_crore >= 0),
    others_folios_crore REAL CHECK(others_folios_crore >= 0)
);

-- Create Index definitions for performance optimizations
CREATE INDEX idx_nav_amfi_date ON fact_nav(amfi_code, date);
CREATE INDEX idx_transactions_amfi ON fact_transactions(amfi_code);
CREATE INDEX idx_transactions_date ON fact_transactions(transaction_date);
CREATE INDEX idx_holdings_amfi ON fact_holdings(amfi_code);
