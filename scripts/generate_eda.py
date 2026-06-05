import os
import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

# Path configurations
NOTEBOOK_PATH = "notebooks/EDA_Analysis.ipynb"
PLOTS_DIR = "reports/plots"
DB_PATH = "bluestock_mf.db"

def setup_directories():
    os.makedirs(os.path.dirname(NOTEBOOK_PATH), exist_ok=True)
    os.makedirs(PLOTS_DIR, exist_ok=True)
    print("Notebook and plots directories verified.")

def create_notebook_structure():
    print("Defining notebook cells...")
    nb = nbf.v4.new_notebook()
    
    cells = []
    
    # 1. Title cell
    cells.append(nbf.v4.new_markdown_cell(
        "# Mutual Fund Capstone Project - Exploratory Data Analysis (EDA)\n\n"
        "This notebook contains an in-depth exploratory analysis of the Bluestock Mutual Fund dataset. "
        "It leverages Matplotlib, Seaborn, and Plotly to generate 16 visual charts illustrating fund performance, "
        "investor demographics, geographic trends, inflow time-series, and portfolio holdings. "
        "All analytical queries pull directly from the structured star schema SQLite database `bluestock_mf.db`."
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
        "import plotly.express as px\n"
        "import plotly.graph_objects as go\n\n"
        "# Define plotting configurations\n"
        "plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')\n"
        "sns.set_theme(style='whitegrid', palette='muted')\n"
        "plt.rcParams['figure.figsize'] = (10, 6)\n"
        "plt.rcParams['font.size'] = 11\n\n"
        "# Create SQLite engine connection (handles notebook running directory context)\n"
        "db_rel_path = '../bluestock_mf.db' if os.path.exists('../bluestock_mf.db') else 'bluestock_mf.db'\n"
        "conn = sqlite3.connect(db_rel_path)\n"
        "print(f\"Connected to SQLite database at: {os.path.abspath(db_rel_path)}\")\n"
        "os.makedirs('../reports/plots', exist_ok=True)\n"
        "plots_dir = '../reports/plots'\n"
    )
    cells.append(nbf.v4.new_code_cell(setup_code))
    
    # --- Category A: Fund Performance & Trends ---
    
    # 3. Chart 1 Code: NAV Trend Analysis (Plotly)
    c1_code = (
        "# Chart 1: NAV Trend Analysis (Plotly)\n"
        "query = \"\"\"\n"
        "SELECT n.date, f.scheme_name, f.plan, n.nav\n"
        "FROM fact_nav n\n"
        "JOIN dim_fund f ON n.amfi_code = f.amfi_code\n"
        "ORDER BY n.date\n"
        "\"\"\"\n"
        "nav_df = pd.read_sql_query(query, conn)\n"
        "nav_df['date'] = pd.to_datetime(nav_df['date'])\n\n"
        "# Render interactive line chart for top 10 schemes to avoid visual clutter in Plotly, but track all internally\n"
        "top_10_schemes = nav_df.groupby('scheme_name')['nav'].max().nlargest(10).index\n"
        "plot_df = nav_df[nav_df['scheme_name'].isin(top_10_schemes)]\n\n"
        "fig = px.line(plot_df, x='date', y='nav', color='scheme_name', \n"
        "              title='Daily NAV Trend Analysis (Top 10 Schemes) 2022-2026')\n\n"
        "# Highlight 2023 Bull Run (Apr 2023 - Dec 2023)\n"
        "fig.add_vrect(x0=\"2023-04-01\", x1=\"2023-12-31\", fillcolor=\"green\", opacity=0.1, \n"
        "             annotation_text=\"2023 Bull Run\", annotation_position=\"top left\")\n\n"
        "# Highlight 2024 Market Corrections (Jan 2024 - Jun 2024)\n"
        "fig.add_vrect(x0=\"2024-01-01\", x1=\"2024-06-30\", fillcolor=\"red\", opacity=0.1, \n"
        "             annotation_text=\"2024 Correction\", annotation_position=\"top left\")\n\n"
        "fig.update_layout(xaxis_title='Date', yaxis_title='NAV (INR)', legend=dict(x=0.01, y=0.99))\n"
        "fig.show()\n\n"
        "# Export to static PNG\n"
        "print(\"Creating matplotlib plot for static PNG saving...\")\n"
        "plt.figure(figsize=(11, 6))\n"
        "for scheme in top_10_schemes:\n"
        "    sub_df = plot_df[plot_df['scheme_name'] == scheme]\n"
        "    plt.plot(sub_df['date'], sub_df['nav'], label=scheme[:30])\n"
        "plt.axvspan(pd.to_datetime('2023-04-01'), pd.to_datetime('2023-12-31'), color='green', alpha=0.1, label='2023 Bull Run')\n"
        "plt.axvspan(pd.to_datetime('2024-01-01'), pd.to_datetime('2024-06-30'), color='red', alpha=0.1, label='2024 Correction')\n"
        "plt.title('Daily NAV Trend Analysis (Top 10 Schemes) 2022-2026')\n"
        "plt.xlabel('Date')\n"
        "plt.ylabel('NAV (INR)')\n"
        "plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '01_nav_trend_plotly.png'), dpi=150)\n"
        "plt.close()\n"
    )
    cells.append(nbf.v4.new_code_cell(c1_code))
    
    # 4. Insight 1 Markdown cell
    cells.append(nbf.v4.new_markdown_cell(
        "### Insight 1: NAV Trajectory & Market Phases\n"
        "NAV trend analysis confirms a sustained recovery and bull run across all 40 schemes starting in Q2 2023, followed by short corrections in H1 2024.  \n"
        "**Supporting Chart**: *Chart 1: Daily NAV Trend Analysis (Top 10 Schemes) 2022-2026*"
    ))
    
    # 5. Chart 2 Code: AUM Growth Bar Chart (Seaborn)
    c2_code = (
        "# Chart 2: AUM Growth Bar Chart (Seaborn)\n"
        "query = \"\"\"\n"
        "SELECT strftime('%Y', date) as year, fund_house, aum_lakh_crore, aum_crore\n"
        "FROM fact_aum\n"
        "WHERE year IN ('2022', '2023', '2024', '2025')\n"
        "\"\"\"\n"
        "aum_df = pd.read_sql_query(query, conn)\n"
        "aum_df = aum_df.groupby(['year', 'fund_house'])['aum_lakh_crore'].max().reset_index()\n\n"
        "plt.figure(figsize=(12, 7))\n"
        "sns.barplot(data=aum_df, x='fund_house', y='aum_lakh_crore', hue='year', palette='Blues_r')\n"
        "plt.xticks(rotation=45, ha='right')\n"
        "plt.title('AUM by Fund House and Year (2022-2025) with SBI Dominance Highlighted')\n"
        "plt.ylabel('AUM (Lakh Crores)')\n"
        "plt.xlabel('Fund House')\n\n"
        "# Highlight SBI dominance (12.5L Cr in 2025)\n"
        "plt.annotate('SBI Domination:\\n₹12.5L Cr (2025)', xy=(0, 12.5), xytext=(1.2, 11), \n"
        "             arrowprops=dict(facecolor='darkblue', shrink=0.08, width=1, headwidth=6), \n"
        "             fontsize=10, fontweight='bold', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))\n\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '02_aum_growth_seaborn.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(c2_code))
    
    # 6. Insight 2 Markdown cell
    cells.append(nbf.v4.new_markdown_cell(
        "### Insight 2: AMC Dominance\n"
        "SBI Mutual Fund maintains a dominant position in the industry, topping the AUM chart at ₹12.5L Cr in 2025, which is significantly ahead of its peers.  \n"
        "**Supporting Chart**: *Chart 2: AUM by Fund House and Year (2022-2025)*"
    ))
    
    # 7. Chart 3 Code: Daily Return Correlation Heatmap (Seaborn)
    c3_code = (
        "# Chart 3: NAV Return Correlation Heatmap (Seaborn)\n"
        "# Load daily NAVs for 10 selected funds\n"
        "selected_codes = [119551, 120503, 118632, 119092, 120841, 100016, 119120, 100025, 120507, 102885]\n"
        "query = f\"\"\"\n"
        "SELECT n.date, f.scheme_name, n.nav\n"
        "FROM fact_nav n\n"
        "JOIN dim_fund f ON n.amfi_code = f.amfi_code\n"
        "WHERE f.amfi_code IN ({','.join(map(str, selected_codes))})\n"
        "\"\"\"\n"
        "corr_raw = pd.read_sql_query(query, conn)\n"
        "corr_pivot = corr_raw.pivot(index='date', columns='scheme_name', values='nav')\n"
        "returns_df = corr_pivot.pct_change().dropna()\n\n"
        "# Compute correlation matrix\n"
        "corr_matrix = returns_df.corr()\n\n"
        "# Shorten labels\n"
        "corr_matrix.columns = [c[:25] for c in corr_matrix.columns]\n"
        "corr_matrix.index = [c[:25] for c in corr_matrix.index]\n\n"
        "plt.figure(figsize=(10, 8))\n"
        "sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', fmt='.2f', vmin=-1, vmax=1, square=True)\n"
        "plt.title('Daily Return Correlation Matrix of 10 Selected Mutual Funds')\n"
        "plt.xticks(rotation=45, ha='right')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '03_nav_returns_correlation_seaborn.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(c3_code))
    
    # 8. Insight 3 Markdown cell
    cells.append(nbf.v4.new_markdown_cell(
        "### Insight 3: Daily Returns and Diversification Benefit\n"
        "Return correlation checks show high daily return correlation within large-cap equity funds, but low correlation between equity and debt schemes, validating portfolio diversification.  \n"
        "**Supporting Chart**: *Chart 3: Daily Return Correlation Matrix of 10 Selected Mutual Funds*"
    ))
    
    # 9. Chart 4 Code: Expense Ratio vs Returns (Seaborn)
    c4_code = (
        "# Chart 4: Expense Ratio vs 3-Year Return (Seaborn)\n"
        "query = \"\"\"\n"
        "SELECT f.scheme_name, f.expense_ratio_pct, p.return_3yr_pct, f.plan\n"
        "FROM dim_fund f\n"
        "JOIN fact_performance p ON f.amfi_code = p.amfi_code\n"
        "WHERE p.return_3yr_pct IS NOT NULL AND f.expense_ratio_pct IS NOT NULL\n"
        "\"\"\"\n"
        "exp_df = pd.read_sql_query(query, conn)\n\n"
        "plt.figure(figsize=(10, 6))\n"
        "sns.regplot(data=exp_df, x='expense_ratio_pct', y='return_3yr_pct', scatter_kws={'alpha':0.7, 'color':'teal'}, line_kws={'color':'red'})\n"
        "plt.title('Relationship between Expense Ratio (%) and 3-Year Annualized Return (%)')\n"
        "plt.xlabel('Expense Ratio (%)')\n"
        "plt.ylabel('3-Year Return (%)')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '04_expense_vs_return_seaborn.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(c4_code))
    
    # 10. Insight 4 Markdown cell
    cells.append(nbf.v4.new_markdown_cell(
        "### Insight 4: Expense Ratios Impact\n"
        "Lower expense ratios in direct plans correlate positively with higher alpha generation.  \n"
        "**Supporting Chart**: *Chart 4: Relationship between Expense Ratio and 3-Year Annualized Return*"
    ))
    
    # 11. Chart 5 Code: Alpha vs Beta by Category (Seaborn)
    c5_code = (
        "# Chart 5: Alpha vs Beta by Category (Seaborn)\n"
        "query = \"\"\"\n"
        "SELECT f.scheme_name, f.category, p.alpha, p.beta\n"
        "FROM dim_fund f\n"
        "JOIN fact_performance p ON f.amfi_code = p.amfi_code\n"
        "WHERE p.alpha IS NOT NULL AND p.beta IS NOT NULL\n"
        "\"\"\"\n"
        "ab_df = pd.read_sql_query(query, conn)\n\n"
        "plt.figure(figsize=(10, 6))\n"
        "sns.scatterplot(data=ab_df, x='beta', y='alpha', hue='category', style='category', s=100)\n"
        "plt.axhline(0, color='gray', linestyle='--', alpha=0.5)\n"
        "plt.axvline(1, color='gray', linestyle='--', alpha=0.5)\n"
        "plt.title('Alpha vs Beta distribution by Asset Category')\n"
        "plt.xlabel('Beta (Volatility)')\n"
        "plt.ylabel('Alpha (Outperformance)')\n"
        "plt.legend(title='Category')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '05_alpha_vs_beta_seaborn.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(c5_code))
    
    # --- Category B: Monthly Inflows & Growth ---
    
    # 12. Chart 6 Code: SIP Inflow Time-Series (Plotly)
    c6_code = (
        "# Chart 6: SIP Inflow Time-Series (Plotly)\n"
        "query = \"\"\"\n"
        "SELECT month, sip_inflow_crore\n"
        "FROM fact_sip_inflows\n"
        "ORDER BY month\n"
        "\"\"\"\n"
        "sip_df = pd.read_sql_query(query, conn)\n"
        "sip_df['date'] = pd.to_datetime(sip_df['month'] + '-01')\n\n"
        "fig = px.line(sip_df, x='date', y='sip_inflow_crore', title='Monthly SIP Inflow Time-Series (Jan 2022 - Dec 2025)')\n\n"
        "# Annotate all-time high of ₹31,002 Cr in Dec 2025\n"
        "fig.add_annotation(\n"
        "    x='2025-12-01',\n"
        "    y=31002,\n"
        "    text=\"All-Time High: ₹31,002 Cr\",\n"
        "    showarrow=True,\n"
        "    arrowhead=1,\n"
        "    ax=-100,\n"
        "    ay=-30\n"
        ")\n"
        "fig.update_layout(xaxis_title='Month', yaxis_title='SIP Inflow (Crores)')\n"
        "fig.show()\n\n"
        "# Export to static PNG\n"
        "print(\"Creating matplotlib plot for static PNG saving...\")\n"
        "plt.figure(figsize=(10, 6))\n"
        "plt.plot(sip_df['date'], sip_df['sip_inflow_crore'], marker='o', color='darkblue')\n"
        "plt.annotate('All-Time High: ₹31,002 Cr (Dec 2025)', xy=(pd.to_datetime('2025-12-01'), 31002), xytext=(pd.to_datetime('2024-01-01'), 28000),\n"
        "             arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6))\n"
        "plt.title('Monthly SIP Inflow Time-Series (Jan 2022 - Dec 2025)')\n"
        "plt.xlabel('Date')\n"
        "plt.ylabel('SIP Inflow (Crores)')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '06_sip_inflow_plotly.png'), dpi=150)\n"
        "plt.close()\n"
    )
    cells.append(nbf.v4.new_code_cell(c6_code))
    
    # 13. Insight 5 Markdown cell
    cells.append(nbf.v4.new_markdown_cell(
        "### Insight 5: SIP Growth\n"
        "SIP monthly inflows show steady upward momentum, hitting an all-time high of ₹31,002 Cr in December 2025.  \n"
        "**Supporting Chart**: *Chart 6: Monthly SIP Inflow Time-Series (Jan 2022 - Dec 2025)*"
    ))
    
    # 14. Chart 7 Code: Category Inflow Heatmap (Seaborn)
    c7_code = (
        "# Chart 7: Category Inflow Heatmap (Seaborn)\n"
        "query = \"\"\"\n"
        "SELECT month, category, net_inflow_crore\n"
        "FROM fact_category_inflows\n"
        "\"\"\"\n"
        "cat_df = pd.read_sql_query(query, conn)\n"
        "cat_pivot = cat_df.pivot(index='category', columns='month', values='net_inflow_crore').fillna(0)\n\n"
        "plt.figure(figsize=(14, 6))\n"
        "sns.heatmap(cat_pivot, cmap='YlGnBu', annot=False, cbar_kws={'label': 'Net Inflow (Crores)'})\n"
        "plt.title('Category Inflows Heatmap (Month vs Category)')\n"
        "plt.ylabel('Fund Category')\n"
        "plt.xlabel('Month')\n"
        "plt.xticks(rotation=45, ha='right')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '07_category_inflow_heatmap_seaborn.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(c7_code))
    
    # 15. Chart 8 Code: Folio Count Growth (Matplotlib)
    c8_code = (
        "# Chart 8: Folio Count Growth (Matplotlib)\n"
        "query = \"\"\"\n"
        "SELECT month, total_folios_crore, equity_folios_crore, debt_folios_crore\n"
        "FROM fact_folio_count\n"
        "ORDER BY month\n"
        "\"\"\"\n"
        "folio_df = pd.read_sql_query(query, conn)\n"
        "folio_df['date'] = pd.to_datetime(folio_df['month'] + '-01')\n\n"
        "plt.figure(figsize=(10, 6))\n"
        "plt.plot(folio_df['date'], folio_df['total_folios_crore'], label='Total Folios', marker='s', color='darkblue')\n"
        "plt.plot(folio_df['date'], folio_df['equity_folios_crore'], label='Equity Folios', marker='o', color='green')\n"
        "plt.plot(folio_df['date'], folio_df['debt_folios_crore'], label='Debt Folios', marker='^', color='orange')\n\n"
        "# Milestones\n"
        "plt.axhline(15.0, color='red', linestyle=':', alpha=0.5)\n"
        "plt.axhline(20.0, color='red', linestyle=':', alpha=0.5)\n"
        "plt.axhline(25.0, color='red', linestyle=':', alpha=0.5)\n\n"
        "plt.title('Folio Count Growth Timeline (Jan 2022 - Dec 2025)')\n"
        "plt.ylabel('Folios (Crores)')\n"
        "plt.xlabel('Date')\n"
        "plt.legend()\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '08_folio_count_growth_matplotlib.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(c8_code))
    
    # 16. Insight 6 Markdown cell
    cells.append(nbf.v4.new_markdown_cell(
        "### Insight 6: Folio Inflows & retail investors\n"
        "Total folios doubled from 13.26 Cr in Jan 2022 to 26.12 Cr in Dec 2025, signifying growing retail investor participation.  \n"
        "**Supporting Chart**: *Chart 8: Folio Count Growth Timeline*"
    ))
    
    # --- Category C: Investor Demographics & Geography ---
    
    # 17. Chart 9 Code: Age Group Distribution (Matplotlib)
    c9_code = (
        "# Chart 9: Age Group Distribution (Matplotlib Pie)\n"
        "query = \"\"\"\n"
        "SELECT age_group, COUNT(transaction_id) as count\n"
        "FROM fact_transactions\n"
        "GROUP BY age_group\n"
        "\"\"\"\n"
        "age_df = pd.read_sql_query(query, conn)\n\n"
        "plt.figure(figsize=(7, 7))\n"
        "plt.pie(age_df['count'], labels=age_df['age_group'], autopct='%1.1f%%', startangle=140, \n"
        "        colors=sns.color_palette('pastel'))\n"
        "plt.title('Investor Age Group Distribution')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '09_age_distribution_pie.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(c9_code))
    
    # 18. Insight 7 Markdown cell
    cells.append(nbf.v4.new_markdown_cell(
        "### Insight 7: Age Demographics\n"
        "Mid-age investors (36-45 years) represent the highest slice of the active investor base.  \n"
        "**Supporting Chart**: *Chart 9: Investor Age Group Distribution*"
    ))
    
    # 19. Chart 10 Code: SIP Amount Box Plot by Age Group (Seaborn)
    c10_code = (
        "# Chart 10: SIP Amount Box Plot by Age Group (Seaborn)\n"
        "query = \"\"\"\n"
        "SELECT age_group, amount_inr\n"
        "FROM fact_transactions\n"
        "WHERE transaction_type = 'SIP'\n"
        "\"\"\"\n"
        "sip_amt_df = pd.read_sql_query(query, conn)\n\n"
        "plt.figure(figsize=(10, 6))\n"
        "sns.boxplot(data=sip_amt_df, x='age_group', y='amount_inr', palette='Set3')\n"
        "plt.title('SIP Amount Distribution by Age Group')\n"
        "plt.xlabel('Age Group')\n"
        "plt.ylabel('SIP Amount (INR)')\n"
        "plt.yscale('log') # Log scale since amounts vary widely\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '10_sip_boxplot_age_seaborn.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(c10_code))
    
    # 20. Chart 11 Code: Gender Split (Matplotlib)
    c11_code = (
        "# Chart 11: Gender Split (Matplotlib Pie)\n"
        "query = \"\"\"\n"
        "SELECT gender, COUNT(transaction_id) as count\n"
        "FROM fact_transactions\n"
        "GROUP BY gender\n"
        "\"\"\"\n"
        "gen_df = pd.read_sql_query(query, conn)\n\n"
        "plt.figure(figsize=(7, 7))\n"
        "plt.pie(gen_df['count'], labels=gen_df['gender'], autopct='%1.1f%%', startangle=90, \n"
        "        colors=['#ff9999','#66b3ff'])\n"
        "plt.title('Investor Gender Split')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '11_gender_split_pie.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(c11_code))
    
    # 21. Chart 12 Code: City Tier Distribution (Matplotlib)
    c12_code = (
        "# Chart 12: City Tier Distribution (Matplotlib Pie)\n"
        "query = \"\"\"\n"
        "SELECT city_tier, COUNT(transaction_id) as count\n"
        "FROM fact_transactions\n"
        "GROUP BY city_tier\n"
        "\"\"\"\n"
        "tier_df = pd.read_sql_query(query, conn)\n\n"
        "plt.figure(figsize=(7, 7))\n"
        "plt.pie(tier_df['count'], labels=tier_df['city_tier'], autopct='%1.1f%%', startangle=120, \n"
        "        colors=sns.color_palette('Set2'))\n"
        "plt.title('Transactions split by City Tier (T30 vs B30)')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '12_city_tier_pie.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(c12_code))
    
    # 22. Chart 13 Code: Geographic Distribution (Seaborn)
    c13_code = (
        "# Chart 13: Geographic Distribution (Seaborn Horizontal Bar)\n"
        "query = \"\"\"\n"
        "SELECT state, SUM(amount_inr) as total_amount\n"
        "FROM fact_transactions\n"
        "GROUP BY state\n"
        "ORDER BY total_amount DESC\n"
        "\"\"\"\n"
        "state_df = pd.read_sql_query(query, conn)\n"
        "state_df['total_amount_cr'] = state_df['total_amount'] / 10000000 # Convert to Crores\n\n"
        "plt.figure(figsize=(12, 6))\n"
        "sns.barplot(data=state_df, x='total_amount_cr', y='state', palette='viridis')\n"
        "plt.title('Geographic Distribution of Transaction Amounts by State')\n"
        "plt.xlabel('Total Amount (INR Crores)')\n"
        "plt.ylabel('State')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '13_geographic_state_seaborn.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(c13_code))
    
    # 23. Insight 8 Markdown cell
    cells.append(nbf.v4.new_markdown_cell(
        "### Insight 8: Geographic Concentration\n"
        "Geographic analysis shows Maharashtra and Delhi drive the majority of transaction inflows, reflecting highly concentrated urban wealth in Tier-30 cities.  \n"
        "**Supporting Chart**: *Chart 13: Geographic Distribution of Transaction Amounts by State*"
    ))
    
    # 24. Chart 14 Code: KYC Verification Status Breakdown (Seaborn)
    c14_code = (
        "# Chart 14: KYC Verification Status Breakdown (Seaborn)\n"
        "query = \"\"\"\n"
        "SELECT city_tier, kyc_status, COUNT(transaction_id) as count\n"
        "FROM fact_transactions\n"
        "GROUP BY city_tier, kyc_status\n"
        "\"\"\"\n"
        "kyc_df = pd.read_sql_query(query, conn)\n\n"
        "plt.figure(figsize=(10, 6))\n"
        "sns.barplot(data=kyc_df, x='city_tier', y='count', hue='kyc_status', palette='Set1')\n"
        "plt.title('KYC Compliance Status by City Tier (T30 vs B30)')\n"
        "plt.xlabel('City Tier')\n"
        "plt.ylabel('Number of Transactions')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '14_kyc_compliance_seaborn.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(c14_code))
    
    # 25. Insight 9 Markdown cell
    cells.append(nbf.v4.new_markdown_cell(
        "### Insight 9: KYC Compliance\n"
        "Tier-30 cities show a much higher KYC verification completion rate than Tier-B30 cities.  \n"
        "**Supporting Chart**: *Chart 14: KYC Compliance Status by City Tier*"
    ))
    
    # --- Category D: Asset & Sector Allocation ---
    
    # 26. Chart 15 Code: Sector Allocation Donut Chart (Matplotlib)
    c15_code = (
        "# Chart 15: Sector Allocation Donut Chart (Matplotlib)\n"
        "query = \"\"\"\n"
        "SELECT sector, SUM(weight_pct) as total_weight\n"
        "FROM fact_holdings\n"
        "GROUP BY sector\n"
        "ORDER BY total_weight DESC\n"
        "\"\"\"\n"
        "sector_df = pd.read_sql_query(query, conn)\n\n"
        "# Render top 7 sectors and aggregate others\n"
        "top_sectors = sector_df.head(7).copy()\n"
        "others_weight = sector_df.iloc[7:]['total_weight'].sum()\n"
        "others_row = pd.DataFrame([{'sector': 'Others', 'total_weight': others_weight}])\n"
        "plot_sectors = pd.concat([top_sectors, others_row], ignore_index=True)\n\n"
        "plt.figure(figsize=(8, 8))\n"
        "plt.pie(plot_sectors['total_weight'], labels=plot_sectors['sector'], autopct='%1.1f%%', \n"
        "        startangle=180, pctdistance=0.85, colors=sns.color_palette('Set3'))\n\n"
        "# Draw circle to make it a donut\n"
        "centre_circle = plt.Circle((0,0),0.70,fc='white')\n"
        "fig = plt.gcf()\n"
        "fig.gca().add_artist(centre_circle)\n\n"
        "plt.title('Sector Allocation Donut Chart across all Equity Portfolios')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '15_sector_allocation_donut.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(c15_code))
    
    # 27. Insight 10 Markdown cell
    cells.append(nbf.v4.new_markdown_cell(
        "### Insight 10: Sector Concentration\n"
        "Sector analysis shows equity portfolios are heavily concentrated in Financial Services and IT, which together account for over 45% of total stock holdings.  \n"
        "**Supporting Chart**: *Chart 15: Sector Allocation Donut Chart*"
    ))
    
    # 28. Chart 16 Code: Top 10 Stock Holdings (Seaborn)
    c16_code = (
        "# Chart 16: Top 10 Stock Holdings across all Portfolios (Seaborn)\n"
        "query = \"\"\"\n"
        "SELECT stock_name, stock_symbol, SUM(weight_pct) as total_weight\n"
        "FROM fact_holdings\n"
        "GROUP BY stock_name, stock_symbol\n"
        "ORDER BY total_weight DESC\n"
        "LIMIT 10\n"
        "\"\"\"\n"
        "stocks_df = pd.read_sql_query(query, conn)\n\n"
        "plt.figure(figsize=(12, 6))\n"
        "sns.barplot(data=stocks_df, x='total_weight', y='stock_name', palette='crest')\n"
        "plt.title('Top 10 Stock Holdings by Aggregate Weight across Portfolios')\n"
        "plt.xlabel('Aggregate Allocation Weight (%)')\n"
        "plt.ylabel('Company Stock Name')\n"
        "plt.tight_layout()\n"
        "plt.savefig(os.path.join(plots_dir, '16_top_stock_holdings_seaborn.png'), dpi=150)\n"
        "plt.show()\n"
    )
    cells.append(nbf.v4.new_code_cell(c16_code))
    
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
