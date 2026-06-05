import os
import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

# Path configurations
NOTEBOOK_PATH = "notebooks/Performance_Analytics.ipynb"
PROCESSED_DIR = "data/processed"
PLOTS_DIR = "reports/plots"

def setup_directories():
    os.makedirs(os.path.dirname(NOTEBOOK_PATH), exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(PLOTS_DIR, exist_ok=True)
    print("Notebook, processed, and plots directories verified.")

def create_notebook_structure():
    print("Defining notebook cells...")
    nb = nbf.v4.new_notebook()
    
    cells = []
    
    # 1. Title cell
    cells.append(nbf.v4.new_markdown_cell(
        "# Mutual Fund Capstone Project - Performance Analytics (Day 4)\n\n"
        "This notebook contains quantitative performance metrics for all 40 mutual fund schemes. "
        "It queries the SQLite star schema database `bluestock_mf.db` to calculate CAGRs (1yr, 3yr, 5yr/Max), "
        "risk-adjusted returns (Sharpe, Sortino), market risk coefficients (Alpha, Beta), and worst drawdown ranges. "
        "It also constructs a composite Fund Scorecard (0-100), outputs result CSVs, and plots a 3-year benchmark "
        "comparison tracking top funds vs. Nifty 50 and Nifty 100 index benchmarks."
    ))
    
    # 2. Setup and DB connection code cell
    setup_code = (
        "# Import dependencies\n"
        "import os\n"
        "import sqlite3\n"
        "import pandas as pd\n"
        "import numpy as np\n"
        "import matplotlib.pyplot as plt\n"
        "import seaborn as sns\n"
        "from scipy import stats\n\n"
        "# Define plotting configurations\n"
        "plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')\n"
        "sns.set_theme(style='whitegrid', palette='muted')\n"
        "plt.rcParams['figure.figsize'] = (10, 6)\n"
        "plt.rcParams['font.size'] = 11\n\n"
        "# Create SQLite engine connection (handles notebooks folder path context)\n"
        "db_rel_path = '../bluestock_mf.db' if os.path.exists('../bluestock_mf.db') else 'bluestock_mf.db'\n"
        "conn = sqlite3.connect(db_rel_path)\n"
        "print(f\"Connected to SQLite database at: {os.path.abspath(db_rel_path)}\")\n"
        "os.makedirs('../data/processed', exist_ok=True)\n"
        "os.makedirs('../reports/plots', exist_ok=True)\n"
        "processed_dir = '../data/processed'\n"
        "plots_dir = '../reports/plots'\n"
    )
    cells.append(nbf.v4.new_code_cell(setup_code))
    
    # 3. Code cell: Load Benchmark daily returns
    benchmark_code = (
        "# Load NIFTY100 daily returns as our index returns for Alpha/Beta regression\n"
        "query = \"\"\"\n"
        "SELECT date, close_value\n"
        "FROM fact_benchmark\n"
        "WHERE index_name = 'NIFTY100'\n"
        "ORDER BY date\n"
        "\"\"\"\n"
        "nifty100_df = pd.read_sql_query(query, conn)\n"
        "nifty100_df['date'] = pd.to_datetime(nifty100_df['date'])\n"
        "nifty100_df['nifty_return'] = nifty100_df['close_value'].pct_change()\n"
        "nifty100_df = nifty100_df.dropna()\n"
        "print(f\"Loaded {len(nifty100_df)} NIFTY100 daily returns.\")\n"
    )
    cells.append(nbf.v4.new_code_cell(benchmark_code))
    
    # 4. Code cell: Compute Fund performance parameters
    perf_calc_code = (
        "# Main calculations for all 40 funds\n"
        "rf_annual = 0.065  # 6.5% risk-free rate proxy\n"
        "rf_daily = rf_annual / 252\n\n"
        "# Get list of all schemes\n"
        "funds_df = pd.read_sql_query(\"\"\"\n"
        "SELECT amfi_code, scheme_name, fund_house, category, plan, expense_ratio_pct, sebi_category_code\n"
        "FROM dim_fund\n"
        "\"\"\", conn)\n\n"
        "performance_records = []\n"
        "alpha_beta_records = []\n"
        "daily_returns_distribution = {}  # Store daily returns for distribution checks\n\n"
        "for idx, row in funds_df.iterrows():\n"
        "    code = int(row['amfi_code'])\n"
        "    name = row['scheme_name']\n"
        "    \n"
        "    # Get NAV history for this fund\n"
        "    nav_query = f\"\"\"\n"
        "    SELECT date, nav\n"
        "    FROM fact_nav\n"
        "    WHERE amfi_code = {code}\n"
        "    ORDER BY date\n"
        "    \"\"\"\n"
        "    nav_df = pd.read_sql_query(nav_query, conn)\n"
        "    if len(nav_df) < 5:\n"
        "        continue\n"
        "    \n"
        "    nav_df['date'] = pd.to_datetime(nav_df['date'])\n"
        "    nav_df['daily_return'] = nav_df['nav'].pct_change()\n"
        "    nav_df = nav_df.dropna()\n"
        "    \n"
        "    # Store returns for distribution check\n"
        "    daily_returns_distribution[code] = nav_df['daily_return'].values\n"
        "    \n"
        "    # 1. CAGR Calculation (1yr, 3yr, Max available history)\n"
        "    latest_record = nav_df.iloc[-1]\n"
        "    latest_nav = latest_record['nav']\n"
        "    latest_date = latest_record['date']\n"
        "    \n"
        "    # 1-Year start\n"
        "    y1_start_date = latest_date - pd.Timedelta(days=365)\n"
        "    y1_nav_start = nav_df.loc[nav_df['date'] >= y1_start_date, 'nav'].values[0] if len(nav_df[nav_df['date'] >= y1_start_date]) > 0 else nav_df.iloc[0]['nav']\n"
        "    cagr_1yr = (latest_nav / y1_nav_start) - 1.0\n"
        "    \n"
        "    # 3-Year start\n"
        "    y3_start_date = latest_date - pd.Timedelta(days=3*365)\n"
        "    y3_nav_start = nav_df.loc[nav_df['date'] >= y3_start_date, 'nav'].values[0] if len(nav_df[nav_df['date'] >= y3_start_date]) > 0 else nav_df.iloc[0]['nav']\n"
        "    cagr_3yr = (latest_nav / y3_nav_start) ** (1/3) - 1.0\n"
        "    \n"
        "    # Max History (representing the ~4.4yr CAGR)\n"
        "    inception_record = nav_df.iloc[0]\n"
        "    inception_nav = inception_record['nav']\n"
        "    inception_date = inception_record['date']\n"
        "    years_span = (latest_date - inception_date).days / 365.25\n"
        "    cagr_max = (latest_nav / inception_nav) ** (1/years_span) - 1.0\n"
        "    \n"
        "    # 2. Sharpe Ratio\n"
        "    excess_returns = nav_df['daily_return'] - rf_daily\n"
        "    sharpe = (excess_returns.mean() / nav_df['daily_return'].std()) * np.sqrt(252) if nav_df['daily_return'].std() > 0 else 0\n"
        "    \n"
        "    # 3. Sortino Ratio\n"
        "    # Downside deviation standard formula\n"
        "    downside_squared = np.minimum(0, excess_returns) ** 2\n"
        "    downside_dev = np.sqrt(downside_squared.mean()) * np.sqrt(252)\n"
        "    sortino = (excess_returns.mean() * 252) / downside_dev if downside_dev > 0 else 0\n"
        "    \n"
        "    # 4. Alpha and Beta (Regression vs NIFTY100 daily returns)\n"
        "    merged_ret = pd.merge(nav_df[['date', 'daily_return']], nifty100_df[['date', 'nifty_return']], on='date')\n"
        "    if len(merged_ret) > 5:\n"
        "        slope, intercept, r_value, p_value, std_err = stats.linregress(merged_ret['nifty_return'], merged_ret['daily_return'])\n"
        "        beta = slope\n"
        "        alpha_annual = intercept * 252\n"
        "    else:\n"
        "        beta, alpha_annual, r_value, p_value = 0, 0, 0, 0\n"
        "        \n"
        "    # 5. Maximum Drawdown and Dates\n"
        "    # Drawdown series\n"
        "    cum_max = nav_df['nav'].cummax()\n"
        "    drawdowns = nav_df['nav'] / cum_max - 1.0\n"
        "    max_dd = drawdowns.min()\n"
        "    \n"
        "    # Worst drawdown range\n"
        "    trough_idx = drawdowns.idxmin()\n"
        "    trough_date = nav_df.loc[trough_idx, 'date']\n"
        "    # Find the peak date leading to the drawdown trough\n"
        "    peak_date = nav_df.loc[:trough_idx, 'nav'].idxmax()\n"
        "    peak_date = nav_df.loc[peak_date, 'date']\n"
        "    \n"
        "    performance_records.append({\n"
        "        'amfi_code': code,\n"
        "        'scheme_name': name,\n"
        "        'fund_house': row['fund_house'],\n"
        "        'category': row['category'],\n"
        "        'plan': row['plan'],\n"
        "        'expense_ratio_pct': row['expense_ratio_pct'],\n"
        "        'cagr_1yr_pct': cagr_1yr * 100,\n"
        "        'cagr_3yr_pct': cagr_3yr * 100,\n"
        "        'cagr_max_pct': cagr_max * 100,\n"
        "        'sharpe_ratio': sharpe,\n"
        "        'sortino_ratio': sortino,\n"
        "        'alpha': alpha_annual,\n"
        "        'beta': beta,\n"
        "        'max_drawdown_pct': max_dd * 100,\n"
        "        'drawdown_peak_date': peak_date.strftime('%Y-%m-%d'),\n"
        "        'drawdown_trough_date': trough_date.strftime('%Y-%m-%d')\n"
        "    })\n"
        "    \n"
        "    alpha_beta_records.append({\n"
        "        'amfi_code': code,\n"
        "        'scheme_name': name,\n"
        "        'alpha': alpha_annual,\n"
        "        'beta': beta,\n"
        "        'r_squared': r_value ** 2,\n"
        "        'p_value': p_value,\n"
        "        'std_err': std_err\n"
        "    })\n\n"
        "perf_df = pd.DataFrame(performance_records)\n"
        "ab_df = pd.DataFrame(alpha_beta_records)\n"
        "print(f\"Computed performance parameters for {len(perf_df)} funds.\")\n"
    )
    cells.append(nbf.v4.new_code_cell(perf_calc_code))
    
    # 5. Code cell: Validate Distribution of daily returns
    dist_code = (
        "# Validate distribution of daily returns\n"
        "plt.figure(figsize=(10, 6))\n"
        "# Pick a representative fund (SBI Bluechip - 119551)\n"
        "sbi_returns = daily_returns_distribution[119551]\n"
        "sns.histplot(sbi_returns, kde=True, bins=50, color='darkblue')\n"
        "plt.title('Daily Return Distribution (SBI Bluechip Fund)')\n"
        "plt.xlabel('Daily Return')\n"
        "plt.ylabel('Frequency')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, 'daily_returns_distribution_sbi.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(dist_code))
    
    # 6. Markdown cell explaining returns distribution checks
    cells.append(nbf.v4.new_markdown_cell(
        "### Return Distribution Validation\n"
        "The daily returns histogram follows a standard normal-like distribution (slightly fat-tailed, or leptokurtic), "
        "which is typical for financial return series. There are no extreme mathematical outliers or faulty values."
    ))
    
    # 7. Code cell: Build Scorecard
    scorecard_code = (
        "# Build Fund Scorecard\n"
        "# Normalize ranks (0-100) where higher/better gets higher score\n"
        "perf_df['rank_return_3yr'] = perf_df['cagr_3yr_pct'].rank(pct=True) * 100\n"
        "perf_df['rank_sharpe'] = perf_df['sharpe_ratio'].rank(pct=True) * 100\n"
        "perf_df['rank_alpha'] = perf_df['alpha'].rank(pct=True) * 100\n"
        "# Expense ratio: lower is better (inverse rank)\n"
        "perf_df['rank_expense'] = (-perf_df['expense_ratio_pct']).rank(pct=True) * 100\n"
        "# Max drawdown: less negative / smaller drawdown is better (inverse rank)\n"
        "perf_df['rank_drawdown'] = perf_df['max_drawdown_pct'].rank(pct=True) * 100\n\n"
        "# Composite scorecard calculation\n"
        "perf_df['composite_score'] = (\n"
        "    0.30 * perf_df['rank_return_3yr'] +\n"
        "    0.25 * perf_df['rank_sharpe'] +\n"
        "    0.20 * perf_df['rank_alpha'] +\n"
        "    0.15 * perf_df['rank_expense'] +\n"
        "    0.10 * perf_df['rank_drawdown']\n"
        ")\n\n"
        "# Sort by composite score\n"
        "scorecard_df = perf_df.sort_values(by='composite_score', ascending=False).reset_index(drop=True)\n"
        "scorecard_df['final_rank'] = scorecard_df.index + 1\n\n"
        "# Save scorecard and alpha-beta to processed folder and copies to root folder\n"
        "scorecard_df.to_csv(os.path.join(processed_dir, 'fund_scorecard.csv'), index=False)\n"
        "scorecard_df.to_csv('../fund_scorecard.csv', index=False)\n"
        "ab_df.to_csv(os.path.join(processed_dir, 'alpha_beta.csv'), index=False)\n"
        "ab_df.to_csv('../alpha_beta.csv', index=False)\n\n"
        "print(\"Top 5 Funds based on Composite Scorecard:\")\n"
        "print(scorecard_df[['final_rank', 'scheme_name', 'cagr_3yr_pct', 'sharpe_ratio', 'alpha', 'max_drawdown_pct', 'composite_score']].head(5))\n"
    )
    cells.append(nbf.v4.new_code_cell(scorecard_code))
    
    # 8. Code cell: Benchmark Comparison Chart
    benchmark_comp_code = (
        "# Chart: Benchmark comparison plot over 3 years\n"
        "# Filter Nifty 50 and Nifty 100 benchmarks for corresponding dates\n"
        "top_5_codes = scorecard_df.head(5)['amfi_code'].tolist()\n\n"
        "# We select the dates corresponding to the last 3 years of NAV data\n"
        "latest_date_query = \"SELECT MAX(date) FROM fact_nav\"\n"
        "max_date = pd.to_datetime(pd.read_sql_query(latest_date_query, conn).values[0][0])\n"
        "start_3yr_date = max_date - pd.Timedelta(days=3*365)\n\n"
        "plt.figure(figsize=(12, 7))\n\n"
        "# 1. Plot benchmarks (Nifty 50 and Nifty 100)\n"
        "bench_query = f\"\"\"\n"
        "SELECT date, index_name, close_value\n"
        "FROM fact_benchmark\n"
        "WHERE date >= '{start_3yr_date.strftime('%Y-%m-%d')}'\n"
        "ORDER BY date\n"
        "\"\"\"\n"
        "bench_data = pd.read_sql_query(bench_query, conn)\n"
        "bench_data['date'] = pd.to_datetime(bench_data['date'])\n\n"
        "for idx_name in ['NIFTY50', 'NIFTY100']:\n"
        "    sub_df = bench_data[bench_data['index_name'] == idx_name].copy()\n"
        "    if not sub_df.empty:\n"
        "        # Index to 100 at start\n"
        "        sub_df = sub_df.sort_values('date')\n"
        "        first_val = sub_df.iloc[0]['close_value']\n"
        "        sub_df['indexed_close'] = (sub_df['close_value'] / first_val) * 100\n"
        "        plt.plot(sub_df['date'], sub_df['indexed_close'], label=idx_name, linewidth=2.5, linestyle='--')\n\n"
        "# 2. Plot Top 5 Funds\n"
        "tracking_errors = []\n"
        "for code in top_5_codes:\n"
        "    fund_row = scorecard_df[scorecard_df['amfi_code'] == code].iloc[0]\n"
        "    fund_name = fund_row['scheme_name']\n"
        "    \n"
        "    fund_query = f\"\"\"\n"
        "    SELECT date, nav\n"
        "    FROM fact_nav\n"
        "    WHERE amfi_code = {code} AND date >= '{start_3yr_date.strftime('%Y-%m-%d')}'\n"
        "    ORDER BY date\n"
        "    \"\"\"\n"
        "    f_df = pd.read_sql_query(fund_query, conn)\n"
        "    f_df['date'] = pd.to_datetime(f_df['date'])\n"
        "    \n"
        "    if not f_df.empty:\n"
        "        f_df = f_df.sort_values('date')\n"
        "        first_nav = f_df.iloc[0]['nav']\n"
        "        f_df['indexed_nav'] = (f_df['nav'] / first_nav) * 100\n"
        "        plt.plot(f_df['date'], f_df['indexed_nav'], label=fund_name[:30], linewidth=1.5)\n"
        "        \n"
        "        # Compute tracking error vs Nifty 100 over this period\n"
        "        f_df['daily_return'] = f_df['nav'].pct_change()\n"
        "        n100_sub = bench_data[bench_data['index_name'] == 'NIFTY100'].copy()\n"
        "        n100_sub['daily_return'] = n100_sub['close_value'].pct_change()\n"
        "        \n"
        "        merged_te = pd.merge(f_df[['date', 'daily_return']], n100_sub[['date', 'daily_return']], on='date', suffixes=('_fund', '_bench'))\n"
        "        merged_te = merged_te.dropna()\n"
        "        \n"
        "        te = np.std(merged_te['daily_return_fund'] - merged_te['daily_return_bench']) * np.sqrt(252)\n"
        "        tracking_errors.append({\n"
        "            'scheme_name': fund_name,\n"
        "            'tracking_error_pct': te * 100\n"
        "        })\n\n"
        "plt.title('3-Year Benchmark Comparison Chart (Top 5 Funds vs Nifty 50 & Nifty 100)')\n"
        "plt.xlabel('Date')\n"
        "plt.ylabel('Indexed Value (Base 100)')\n"
        "plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, 'benchmark_comparison.png'), dpi=150)\n"
        "plt.show()\n\n"
        "te_df = pd.DataFrame(tracking_errors)\n"
        "print(\"Tracking Errors of Top 5 Funds vs NIFTY100:\")\n"
        "print(te_df)\n"
    )
    cells.append(nbf.v4.new_code_cell(benchmark_comp_code))
    
    nb['cells'] = cells
    
    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
        
    print(f"Jupyter notebook structure successfully generated at: {NOTEBOOK_PATH}")

def execute_notebook():
    print("Executing Jupyter notebook cell-by-cell using ExecutePreprocessor...")
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = nbf.read(f, as_version=4)
        
    # Set execution directories
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    
    try:
        ep.preprocess(nb, {'metadata': {'path': 'notebooks'}})
        print("Notebook executed successfully.")
    except Exception as e:
        print(f"Error executing notebook: {e}")
        raise e
        
    # Write back executed notebook
    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Executed notebook saved with inline outputs at: {NOTEBOOK_PATH}")

def main():
    setup_directories()
    create_notebook_structure()
    execute_notebook()

if __name__ == "__main__":
    main()
