# Power BI Setup & Implementation Guide
This guide provides step-by-step instructions to connect, model, and rebuild the **Bluestock Mutual Fund Analytics Dashboard** in Power BI Desktop locally.

---

## 1. Data Connection & Loading
You can connect Power BI to either the cleaned CSV files (located in `data/processed/`) or the SQLite database (`bluestock_mf.db`).

### Option A: Cleaned CSVs (Recommended)
1. In Power BI Desktop, click **Get Data** -> **Text/CSV**.
2. Import all 10 processed CSV files from `data/processed/`:
   - `01_fund_master.csv` (Dim Fund)
   - `02_nav_history.csv` (Fact NAV)
   - `03_aum_by_fund_house.csv` (Fact AUM)
   - `04_monthly_sip_inflows.csv` (Fact SIP Inflows)
   - `05_category_inflows.csv` (Fact Category Inflows)
   - `06_industry_folio_count.csv` (Fact Folio Count)
   - `07_scheme_performance.csv` (Fact Performance / Scorecard)
   - `08_investor_transactions.csv` (Fact Transactions)
   - `09_portfolio_holdings.csv` (Fact Holdings)
   - `10_benchmark_indices.csv` (Fact Benchmark)
3. Use the Power Query Editor to check column types (specifically ensure dates are set as Date type and numeric columns as Decimal/Whole number).

### Option B: SQLite Database Connection
1. Install the **SQLite ODBC Driver** (e.g. from Christian Werner's site).
2. Open Windows **ODBC Data Source Administrator** (64-bit) and add a new System DSN named `BluestockMF` pointing to `C:\Bluestock\bluestock_mf.db`.
3. In Power BI, click **Get Data** -> **ODBC**, select `BluestockMF`, and select the 10 tables to load.

---

## 2. Entity-Relationship Modeling (Star Schema)
Power BI will automatically detect some relationships, but you must verify or construct the following relationships in the **Model View** to enable correct filtering:

### Relationships on `amfi_code`
* `dim_fund[amfi_code]` (1) &rarr; `fact_nav[amfi_code]` (*)
* `dim_fund[amfi_code]` (1) &rarr; `fact_transactions[amfi_code]` (*)
* `dim_fund[amfi_code]` (1) &rarr; `fact_performance[amfi_code]` (1-to-1)
* `dim_fund[amfi_code]` (1) &rarr; `fact_holdings[amfi_code]` (*)

### Relationships on `date`
Create a custom Date table (or use a loaded `dim_date` table) and link it:
* `dim_date[date]` (1) &rarr; `fact_nav[date]` (*)
* `dim_date[date]` (1) &rarr; `fact_transactions[transaction_date]` (*)
* `dim_date[date]` (1) &rarr; `fact_aum[date]` (*)
* `dim_date[date]` (1) &rarr; `fact_benchmark[date]` (*)
* `dim_date[date]` (1) &rarr; `fact_holdings[portfolio_date]` (*)

### Month-Grain Tables
For tables containing `month` columns in `YYYY-MM` format (e.g. `fact_sip_inflows`, `fact_category_inflows`, `fact_folio_count`):
1. In Power Query, transform the `month` column into a Date type (Power BI will automatically convert `2024-05` to `2024-05-01`).
2. Establish a relationship from `dim_date[date]` (1) to `fact_table[month]` (*).

---

## 3. DAX Formulations (Measures & KPIs)
Create a new table `_Measures` and add the following DAX calculations:

### KPI 1: Total Assets Under Management (AUM)
Sum the AUM of all fund houses on the latest recorded snapshot date.
```dax
Total AUM (Lakh Cr) = 
VAR LatestDate = MAX(fact_aum[date])
RETURN
    CALCULATE(
        SUM(fact_aum[aum_crore]) / 100000,
        fact_aum[date] = LatestDate
    )
```

### KPI 2: Latest Monthly SIP Inflows
Retrieve the SIP inflow value for the most recent month.
```dax
Latest SIP Inflow (Cr) = 
VAR LatestMonth = MAX(fact_sip_inflows[month])
RETURN
    CALCULATE(
        SUM(fact_sip_inflows[sip_inflow_crore]),
        fact_sip_inflows[month] = LatestMonth
    )
```

### KPI 3: Active Folio Count
```dax
Total Folios (Cr) = 
VAR LatestMonth = MAX(fact_folio_count[month])
RETURN
    CALCULATE(
        SUM(fact_folio_count[total_folios_crore]),
        fact_folio_count[month] = LatestMonth
    )
```

### KPI 4: Active Mutual Fund Schemes
Sum the scheme counts across all AMCs on the latest recorded date.
```dax
Active Schemes = 
VAR LatestDate = MAX(fact_aum[date])
RETURN
    CALCULATE(
        SUM(fact_aum[num_schemes]),
        fact_aum[date] = LatestDate
    )
```

---

## 4. Visual Layout Configurations

### Page 1: Industry Overview
1. **KPI Cards**: Place four Card visuals at the top of the page using the measures:
   - `Total AUM (Lakh Cr)` &rarr; Format as: `₹81.25L Cr`
   - `Latest SIP Inflow (Cr)` &rarr; Format as: `₹31,002 Cr`
   - `Total Folios (Cr)` &rarr; Format as: `26.12 Cr`
   - `Active Schemes` &rarr; Format as: `1,908`
2. **Line Chart (Industry AUM Trend)**:
   - **Axis**: `dim_date[month]` or `fact_aum[date]` (aggregated by Month/Year)
   - **Values**: `SUM(fact_aum[aum_crore])`
3. **Bar Chart (AUM by AMC)**:
   - **Y-Axis**: `fact_aum[fund_house]`
   - **X-Axis**: `SUM(fact_aum[aum_crore])` (Filtered to the latest date)

### Page 2: Fund Performance
1. **Scatter Plot (Risk vs Return)**:
   - **X-Axis**: `fact_performance[return_3yr_pct]`
   - **Y-Axis**: `fact_performance[std_dev_ann_pct]`
   - **Size**: `fact_performance[aum_crore]`
   - **Legend**: `dim_fund[category]`
2. **Line Chart (NAV vs. Benchmark)**:
   - **Axis**: `fact_nav[date]`
   - **Values**: `fact_nav[nav]` and `fact_benchmark[close_value]`
   - *Note*: Create a custom DAX measure to reindex NAVs to a base of 100 on start date for clean comparative scaling.
3. **Scorecard Table**:
   - Columns: `dim_fund[scheme_name]`, `dim_fund[fund_house]`, `dim_fund[category]`, `fact_performance[return_3yr_pct]`, `fact_performance[sharpe_ratio]`, `fact_performance[alpha]`, `fact_performance[expense_ratio_pct]`, `fact_performance[max_drawdown_pct]`, `fact_performance[composite_score]` (custom calculated rank).
4. **Slicers**:
   - Add three dropdown slicers: `dim_fund[fund_house]`, `dim_fund[category]`, `dim_fund[plan]`.

### Page 3: Investor Analytics
1. **Bar Chart (Inflows by State)**:
   - **X-Axis**: `fact_transactions[state]`
   - **Y-Axis**: `SUM(fact_transactions[amount_inr])`
2. **Donut Chart (Transaction Split)**:
   - **Legend**: `fact_transactions[transaction_type]`
   - **Values**: `SUM(fact_transactions[amount_inr])`
3. **Bar Chart (Age vs. Average SIP)**:
   - **X-Axis**: `fact_transactions[age_group]`
   - **Y-Axis**: `AVERAGE(fact_transactions[amount_inr])` (Filtered to `transaction_type = "SIP"`)
4. **Line Chart (Monthly Volume)**:
   - **Axis**: `fact_transactions[transaction_date]` (grouped by Month)
   - **Values**: `COUNT(fact_transactions[transaction_id])`
5. **Slicers**:
   - Dropdown slicers: `fact_transactions[state]`, `fact_transactions[age_group]`, `fact_transactions[city_tier]`.

### Page 4: SIP & Market Trends
1. **Dual-Axis Chart (SIP Inflow & Nifty)**:
   - **Axis**: `fact_sip_inflows[month]`
   - **Column Values (Left Y-Axis)**: `SUM(fact_sip_inflows[sip_inflow_crore])`
   - **Line Values (Right Y-Axis)**: `AVERAGE(fact_benchmark[close_value])` (Filtered to `index_name = "NIFTY50"`)
2. **Heatmap Matrix (Category Inflows)**:
   - **Rows**: `fact_category_inflows[category]`
   - **Columns**: `fact_category_inflows[month]`
   - **Values**: `SUM(fact_category_inflows[net_inflow_crore])`
   - *Formatting*: Enable conditional formatting (Color scales) on background color, mapping negative values to Light Red and positive values to Light/Dark Green.
3. **Bar Chart (Top Categories FY25)**:
   - **X-Axis**: `fact_category_inflows[category]`
   - **Y-Axis**: `SUM(fact_category_inflows[net_inflow_crore])` (Filtered to `month` between `2024-04` and `2025-03`).

---

## 5. Adding Interactivity & Drill-Through
To replicate the drill-through behavior:
1. Create a new page named **NAV Detail**.
2. In the **Drill-through** field bucket, drag `dim_fund[amfi_code]`.
3. Add a line chart showing `fact_nav[nav]` and `fact_benchmark[close_value]` over time on the NAV Detail page.
4. On **Page 2 (Fund Performance)**, right-clicking a scheme name in the scorecard table will now display the option: **Drill-through &rarr; NAV Detail**.

---

## 6. Theme Styling
To import the Bluestock brand colors into Power BI:
1. In the **View** tab, click the dropdown under **Themes** and select **Browse for themes**.
2. Create a file named `bluestock_theme.json` with the following contents and load it:
```json
{
    "name": "Bluestock Theme",
    "dataColors": ["#414BEA", "#F05537", "#012970", "#10b981", "#6f74df", "#f59e0b", "#94a3b8", "#e2e8f0"],
    "background": "#FFFFFF",
    "foreground": "#1E293B",
    "tableAccent": "#414BEA"
}
```
3. Drag the Bluestock Logo image (`reports/plots/media__1780504737766.png` or your brand logo) into the header of each page.
