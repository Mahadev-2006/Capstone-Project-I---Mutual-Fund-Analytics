# Bluestock Mutual Fund Analytics & Decision Support System

An end-to-end data engineering and quantitative analytics system designed for **Bluestock Fintech**. This project unifies scattered mutual fund metadata, daily NAV historical data, and investor transaction logs into a optimized SQLite star-schema database, performs financial risk analytics (CAGRs, Sharpe/Sortino ratios, Alpha/Beta regressions, Value at Risk, and Sector HHI concentration), and serves a premium interactive dashboard with automated reporting exports.

---

## 1. System Architecture & Schema Mappings
The data warehouse is built on a relational **Star Schema** to optimize query performance and joins:
* **Dimension Tables**:
  - `dim_fund`: Fund metadata (AMFI code, AMC, plan, risk classification, expense ratio).
  - `dim_date`: Calendar dimension spanning Jan 2022 to May 2026.
* **Fact Tables**:
  - `fact_nav`: Daily historical Net Asset Values (40,000+ rows, forward-filled on market holidays).
  - `fact_transactions`: Retail transaction records (SIP/Lumpsum/Redemption, state, city tier, demographics).
  - `fact_performance`: Pre-computed performance scorecard and risk-adjusted scores.
  - `fact_holdings`: Individual stock weights and sector allocations per fund.
  - `fact_aum` & `fact_sip_inflows`: Market and industry-wide size indicators.

---

## 2. Prerequisites & Local Setup
To run the pipeline locally, you will need a Windows environment with **Python 3.10+** and **Google Chrome** (required for automated PDF/PNG report generation).

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Mahadev-2006/Capstone-Project-I---Mutual-Fund-Analytics.git
   cd Capstone-Project-I---Mutual-Fund-Analytics
   ```
2. **Set up Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   .venv\Scripts\pip.exe install -r requirements.txt
   .venv\Scripts\pip.exe install reportlab python-pptx
   ```

---

## 3. Operational Guide: Running the Pipeline
You can run the entire analytics and ingestion pipeline using the unified master execution script:
```powershell
.venv\Scripts\python.exe run_pipeline.py
```
This script runs the following steps in sequence:
1. **`scripts/data_cleaning.py`**: Reads raw data from `data/raw/`, cleans values, forward-fills calendar gaps for holidays, and saves processed CSVs in `data/processed/`.
2. **`scripts/db_loader.py`**: Formulates the SQLite database `bluestock_mf.db`, loads the star-schema tables, and compiles structural indices.
3. **`scripts/generate_analytics.py`**: Computes CAGRs, Sharpe, Alpha, Beta, maximum drawdowns, and compiles the composite scorecard `fund_scorecard.csv`.
4. **`scripts/generate_advanced_analytics.py`**: Computes VaR/CVaR risk tables, rolling 90-day Sharpe ratios, investor cohorts, SIP continuity rates, sector concentration (HHI), and populates `notebooks/Advanced_Analytics.ipynb`.
5. **`scripts/extract_dashboard_data.py`**: Packages database aggregates into `dashboard/data.js`.
6. **`scripts/generate_report.py`**: Spins up a local HTTP server, captures Chrome screenshots of all 4 dashboard pages, compiles `Dashboard.pdf`, and generates `bluestock_mf_dashboard.pbix`.

---

## 4. Recommender & Final Reports Generation
To run the standalone mutual fund recommender:
```powershell
.venv\Scripts\python.exe recommender.py --risk Moderate
```
*(Options: `Low`, `Moderate`, `High`)*

To compile the final PDF report (19 pages) and PowerPoint presentation:
```powershell
.venv\Scripts\python.exe scripts/generate_final_report.py
.venv\Scripts\python.exe scripts/generate_presentation.py
```

---

## 5. Opening the Interactive Dashboard
The premium interactive dashboard can be opened directly in any web browser without needing a running backend server:
1. Navigate to the `dashboard/` directory.
2. Double-click **`index.html`** to open it.
3. Use the sidebar menu to toggle between the 4 pages:
   - **Page 1: Industry Overview**: High-level assets, monthly inflows, and AMC market sizes.
   - **Page 2: Fund Performance**: Risk vs. Return Bubble chart, scorecard table, and drop-down slicers. *Drill-Through*: Click any row in the scorecard table to open a modal overlay detailing daily NAV history vs. the Nifty 50 benchmark.
   - **Page 3: Investor Analytics**: State inflows bar, purchase/redemption splits, age ticket sizes, and city tier filters.
   - **Page 4: SIP & Market Trends**: Dual-axis SIP vs. Nifty chart, monthly net inflow heatmap, and top categories.

---

## 6. Deliverables List
All generated deliverables are located in the project's root folder:
* **`Final_Report.pdf`**: Comprehensive 19-page business analysis report.
* **`Bluestock_MF_Presentation.pptx`**: 12-slide executive presentation slide deck.
* **`bluestock_mf_dashboard.pbix`**: Structured Power BI report layout template.
* **`Dashboard.pdf`**: Multi-page PDF compilation of the dashboard.
* **`Page1.png` - `Page4.png`**: High-resolution screenshots of the dashboard pages.
* **`var_cvar_report.csv`**: Detailed risk report.
* **`rolling_sharpe_chart.png`**: Line chart showing rolling Sharpe ratio trend.
* **`recommender.py`**: Standalone terminal recommendation engine.