-- queries.sql
-- 10 Analytical SQL Queries for Bluestock Mutual Fund SQLite Database

-- Enable Foreign Key support for current session
PRAGMA foreign_keys = ON;

-- 1. Top 5 funds by AUM
-- Ranks funds by the AUM reported in the latest performance fact table.
SELECT 
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.category,
    p.aum_crore
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;


-- 2. Average NAV per month
-- Computes the average NAV value per month for each scheme code.
SELECT 
    f.amfi_code,
    f.scheme_name,
    d.year,
    d.month,
    d.month_name,
    ROUND(AVG(n.nav), 4) AS avg_nav
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
JOIN dim_date d ON n.date = d.date
GROUP BY f.amfi_code, d.year, d.month
ORDER BY f.amfi_code, d.year, d.month;


-- 3. SIP YoY growth
-- Shows monthly SIP inflows alongside active SIP accounts and Yo-Yo growth (from SIP Inflows table).
SELECT 
    month,
    sip_inflow_crore,
    active_sip_accounts_crore,
    sip_aum_lakh_crore,
    yoy_growth_pct
FROM fact_sip_inflows
ORDER BY month DESC;


-- 4. Transactions by state
-- Counts transaction volumes, total amount, and average transaction size per Indian state.
SELECT 
    state,
    COUNT(transaction_id) AS total_transactions,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr,
    ROUND(AVG(amount_inr), 2) AS average_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;


-- 5. Funds with expense_ratio < 1%
-- Identifies low-cost mutual fund options.
SELECT 
    amfi_code,
    scheme_name,
    fund_house,
    category,
    plan,
    expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0 AND plan = 'Direct'
ORDER BY expense_ratio_pct ASC;


-- 6. Alpha analysis (3-Year Performance vs Benchmark)
-- Ranks funds based on their 3-year Alpha, indicating how much they outperformed their expected benchmark risk.
SELECT 
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.category,
    p.return_3yr_pct,
    p.benchmark_3yr_pct,
    p.alpha
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
ORDER BY p.alpha DESC;


-- 7. Demographic profile (Transaction analysis by Gender and Age Group)
-- Analyzes investor profiles and their total invested amounts.
SELECT 
    gender,
    age_group,
    COUNT(transaction_id) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_invested_inr,
    ROUND(AVG(amount_inr), 2) AS avg_transaction_inr
FROM fact_transactions
GROUP BY gender, age_group
ORDER BY total_invested_inr DESC;


-- 8. Top Sectors by Portfolio holdings weight
-- Ranks the sectors where funds have invested the most, aggregated across all fund holdings.
SELECT 
    sector,
    COUNT(DISTINCT amfi_code) AS funds_holding_sector,
    COUNT(holding_id) AS total_stock_investments,
    ROUND(AVG(weight_pct), 2) AS avg_holding_weight_pct
FROM fact_holdings
GROUP BY sector
ORDER BY avg_holding_weight_pct DESC;


-- 9. KYC status breakdown by City Tier
-- Inspects compliance parameters (KYC status) across tier-based regions.
SELECT 
    city_tier,
    kyc_status,
    COUNT(transaction_id) AS total_transactions,
    ROUND(SUM(amount_inr), 2) AS transaction_volume_inr
FROM fact_transactions
GROUP BY city_tier, kyc_status
ORDER BY city_tier, kyc_status;


-- 10. Low/Moderate Risk funds with High Returns (3-Year Return > 12%)
-- Finds funds with moderate or low risk classifications that produced returns above a 12% benchmark.
SELECT 
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.risk_category,
    p.return_3yr_pct,
    p.sharpe_ratio,
    p.sortino_ratio
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
WHERE f.risk_category IN ('Moderate', 'Low') AND p.return_3yr_pct > 12.0
ORDER BY p.return_3yr_pct DESC;
