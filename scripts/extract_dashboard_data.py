import os
import sqlite3
import json
import pandas as pd
import numpy as np

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

DB_PATH = "C:/Bluestock/bluestock_mf.db"
OUTPUT_PATH = "C:/Bluestock/dashboard/data.js"

def extract_data():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    
    # ----------------------------------------------------
    # Page 1: Industry Overview
    # ----------------------------------------------------
    
    # KPI 1: Total AUM (latest date in fact_aum)
    aum_df = pd.read_sql_query("""
        SELECT date, SUM(aum_crore) as total_aum_crore 
        FROM fact_aum 
        GROUP BY date 
        ORDER BY date DESC 
        LIMIT 1
    """, conn)
    latest_date = aum_df['date'].iloc[0] if not aum_df.empty else "N/A"
    # Convert Crore to Lakh Crore
    total_aum_lakh_cr = round(aum_df['total_aum_crore'].iloc[0] / 100000, 2) if not aum_df.empty else 81.00
    
    # KPI 2: Latest SIP Inflow (latest month in fact_sip_inflows)
    sip_kpi_df = pd.read_sql_query("""
        SELECT month, sip_inflow_crore 
        FROM fact_sip_inflows 
        ORDER BY month DESC 
        LIMIT 1
    """, conn)
    latest_sip_crore = sip_kpi_df['sip_inflow_crore'].iloc[0] if not sip_kpi_df.empty else 31002
    
    # KPI 3: Latest Folios (latest month in fact_folio_count)
    folios_kpi_df = pd.read_sql_query("""
        SELECT month, total_folios_crore 
        FROM fact_folio_count 
        ORDER BY month DESC 
        LIMIT 1
    """, conn)
    latest_folios_cr = folios_kpi_df['total_folios_crore'].iloc[0] if not folios_kpi_df.empty else 26.12
    
    # KPI 4: Schemes Count (Distinct count of AMFI codes in dim_fund, plus industry-wide total)
    schemes_kpi_df = pd.read_sql_query("""
        SELECT SUM(num_schemes) as total_schemes 
        FROM fact_aum 
        WHERE date = ?
    """, conn, params=(latest_date,))
    # Industry level schemes count is around 1908
    industry_schemes = schemes_kpi_df['total_schemes'].iloc[0] if not schemes_kpi_df.empty and schemes_kpi_df['total_schemes'].iloc[0] else 1908
    
    # Industry AUM Trend 2022-2025 (Monthly AUM aggregates)
    # Since AUM snapshots are daily/weekly, we take the last snapshot of each month
    aum_trend_df = pd.read_sql_query("""
        SELECT strftime('%Y-%m', date) as month, SUM(aum_crore) as aum_crore
        FROM fact_aum
        WHERE date IN (
            SELECT MAX(date) 
            FROM fact_aum 
            GROUP BY strftime('%Y-%m', date)
        )
        GROUP BY month
        ORDER BY month ASC
    """, conn)
    # Format and convert to Lakh Crores
    aum_trend = []
    for idx, row in aum_trend_df.iterrows():
        aum_trend.append({
            "month": row['month'],
            "aum_lakh_crore": round(row['aum_crore'] / 100000, 2)
        })
        
    # AUM by AMC (latest snapshot)
    aum_by_amc_df = pd.read_sql_query("""
        SELECT fund_house, aum_crore
        FROM fact_aum
        WHERE date = ?
        ORDER BY aum_crore DESC
    """, conn, params=(latest_date,))
    aum_by_amc = []
    for idx, row in aum_by_amc_df.iterrows():
        aum_by_amc.append({
            "amc": row['fund_house'],
            "aum_lakh_crore": round(row['aum_crore'] / 100000, 2)
        })
        
    # ----------------------------------------------------
    # Page 2: Fund Performance
    # ----------------------------------------------------
    
    # Scatter plot data: Return (3yr) vs Risk (StdDev), size = AUM
    scatter_df = pd.read_sql_query("""
        SELECT f.amfi_code, f.scheme_name, f.fund_house, f.category, f.plan,
               p.return_3yr_pct, p.std_dev_ann_pct, p.aum_crore
        FROM dim_fund f
        JOIN fact_performance p ON f.amfi_code = p.amfi_code
        WHERE p.return_3yr_pct IS NOT NULL AND p.std_dev_ann_pct IS NOT NULL
    """, conn)
    scatter_data = scatter_df.to_dict(orient='records')
    
    # Sortable Fund Scorecard Table (read from fund_scorecard.csv or join tables)
    scorecard_path = "C:/Bluestock/fund_scorecard.csv"
    if os.path.exists(scorecard_path):
        scorecard_df = pd.read_csv(scorecard_path)
    else:
        # Fallback to direct query
        scorecard_df = pd.read_sql_query("""
            SELECT f.amfi_code, f.scheme_name, f.fund_house, f.category, f.plan,
                   p.return_1yr_pct, p.return_3yr_pct, p.return_5yr_pct,
                   p.sharpe_ratio, p.sortino_ratio, p.alpha, p.beta, 
                   p.std_dev_ann_pct, p.max_drawdown_pct, p.aum_crore, p.expense_ratio_pct
            FROM dim_fund f
            JOIN fact_performance p ON f.amfi_code = p.amfi_code
        """, conn)
        
    scorecard_data = scorecard_df.to_dict(orient='records')
    
    # Daily NAV vs Benchmark for the top 5 funds and indexes
    # We will get the list of top 5 funds based on the scorecard (composite score or 3yr return)
    if 'composite_score' in scorecard_df.columns:
        top_5_amfi = scorecard_df.sort_values(by='composite_score', ascending=False)['amfi_code'].head(5).tolist()
    else:
        top_5_amfi = scatter_df.sort_values(by='return_3yr_pct', ascending=False)['amfi_code'].head(5).tolist()
        
    # Get names of top 5 funds
    top_5_names = pd.read_sql_query("""
        SELECT amfi_code, scheme_name FROM dim_fund WHERE amfi_code IN ({})
    """.format(",".join(map(str, top_5_amfi))), conn)
    top_5_names_dict = dict(zip(top_5_names['amfi_code'], top_5_names['scheme_name']))
    
    # Weekly/Monthly downsampled NAV data to avoid huge JS files
    # Let's take weekly NAVs (where day of week is Friday or the closest date)
    nav_df = pd.read_sql_query("""
        SELECT n.amfi_code, n.date, n.nav
        FROM fact_nav n
        JOIN dim_date d ON n.date = d.date
        WHERE n.amfi_code IN ({})
          AND (d.day_name = 'Friday' OR d.day = 1)
        ORDER BY n.date ASC
    """.format(",".join(map(str, top_5_amfi))), conn)
    
    # Benchmark data weekly
    bench_df = pd.read_sql_query("""
        SELECT b.index_name, b.date, b.close_value
        FROM fact_benchmark b
        JOIN dim_date d ON b.date = d.date
        WHERE b.index_name IN ('NIFTY50', 'NIFTY100')
          AND (d.day_name = 'Friday' OR d.day = 1)
        ORDER BY b.date ASC
    """, conn)
    
    nav_history = {}
    for amfi in top_5_amfi:
        fund_navs = nav_df[nav_df['amfi_code'] == amfi]
        nav_history[top_5_names_dict[amfi]] = {
            "dates": fund_navs['date'].tolist(),
            "navs": fund_navs['nav'].tolist()
        }
        
    for index in ['NIFTY50', 'NIFTY100']:
        ind_vals = bench_df[bench_df['index_name'] == index]
        nav_history[index] = {
            "dates": ind_vals['date'].tolist(),
            "values": ind_vals['close_value'].tolist()
        }
        
    # ----------------------------------------------------
    # Page 3: Investor Analytics
    # ----------------------------------------------------
    
    # State-wise transaction amount
    state_trans_df = pd.read_sql_query("""
        SELECT state, SUM(amount_inr) as total_amount
        FROM fact_transactions
        GROUP BY state
        ORDER BY total_amount DESC
    """, conn)
    state_trans = []
    for idx, row in state_trans_df.iterrows():
        state_trans.append({
            "state": row['state'],
            "amount_crore": round(row['total_amount'] / 10000000, 2)
        })
        
    # SIP / Lumpsum / Redemption split
    type_split_df = pd.read_sql_query("""
        SELECT transaction_type, SUM(amount_inr) as total_amount
        FROM fact_transactions
        GROUP BY transaction_type
    """, conn)
    type_split = {}
    total_tx_amount = type_split_df['total_amount'].sum()
    for idx, row in type_split_df.iterrows():
        type_split[row['transaction_type']] = {
            "amount_crore": round(row['total_amount'] / 10000000, 2),
            "percentage": round((row['total_amount'] / total_tx_amount) * 100, 2)
        }
        
    # Age group vs average SIP amount
    age_sip_df = pd.read_sql_query("""
        SELECT age_group, AVG(amount_inr) as avg_sip_amount
        FROM fact_transactions
        WHERE transaction_type = 'SIP'
        GROUP BY age_group
        ORDER BY age_group ASC
    """, conn)
    age_sip = []
    for idx, row in age_sip_df.iterrows():
        age_sip.append({
            "age_group": row['age_group'],
            "avg_sip": round(row['avg_sip_amount'], 2)
        })
        
    # Monthly transaction volume line
    volume_df = pd.read_sql_query("""
        SELECT strftime('%Y-%m', transaction_date) as month, COUNT(*) as tx_count
        FROM fact_transactions
        GROUP BY month
        ORDER BY month ASC
    """, conn)
    volume_trend = []
    for idx, row in volume_df.iterrows():
        volume_trend.append({
            "month": row['month'],
            "count": row['tx_count']
        })
        
    # Slicers lists
    states_list = pd.read_sql_query("SELECT DISTINCT state FROM fact_transactions ORDER BY state", conn)['state'].tolist()
    age_groups_list = pd.read_sql_query("SELECT DISTINCT age_group FROM fact_transactions ORDER BY age_group", conn)['age_group'].tolist()
    city_tiers_list = pd.read_sql_query("SELECT DISTINCT city_tier FROM fact_transactions ORDER BY city_tier", conn)['city_tier'].tolist()
    
    # ----------------------------------------------------
    # Page 4: SIP & Market Trends
    # ----------------------------------------------------
    
    # Monthly SIP inflow (bar) + Nifty 50 close at month-end (line)
    # First get monthly SIP inflows
    sip_inflows_df = pd.read_sql_query("""
        SELECT month, sip_inflow_crore
        FROM fact_sip_inflows
        ORDER BY month ASC
    """, conn)
    
    # Get Nifty 50 month-end values
    nifty_monthly_df = pd.read_sql_query("""
        SELECT strftime('%Y-%m', date) as month, close_value
        FROM fact_benchmark
        WHERE index_name = 'NIFTY50'
          AND date IN (
              SELECT MAX(date)
              FROM fact_benchmark
              WHERE index_name = 'NIFTY50'
              GROUP BY strftime('%Y-%m', date)
          )
        ORDER BY month ASC
    """, conn)
    
    sip_nifty_merge = pd.merge(sip_inflows_df, nifty_monthly_df, on='month', how='inner')
    sip_nifty = []
    for idx, row in sip_nifty_merge.iterrows():
        sip_nifty.append({
            "month": row['month'],
            "sip_inflow_crore": row['sip_inflow_crore'],
            "nifty_close": round(row['close_value'], 2)
        })
        
    # Category net inflow heatmap (Month x Category matrix)
    heatmap_df = pd.read_sql_query("""
        SELECT month, category, net_inflow_crore
        FROM fact_category_inflows
        ORDER BY month ASC, category ASC
    """, conn)
    heatmap_data = heatmap_df.to_dict(orient='records')
    
    # Top 5 categories by net inflow FY25 (Apr 2024 - Mar 2025)
    fy25_inflows_df = pd.read_sql_query("""
        SELECT category, SUM(net_inflow_crore) as net_inflow_fy25
        FROM fact_category_inflows
        WHERE month BETWEEN '2024-04' AND '2025-03'
        GROUP BY category
        ORDER BY net_inflow_fy25 DESC
        LIMIT 5
    """, conn)
    top_categories_fy25 = []
    for idx, row in fy25_inflows_df.iterrows():
        top_categories_fy25.append({
            "category": row['category'],
            "net_inflow_crore": round(row['net_inflow_fy25'], 2)
        })
        
    # ----------------------------------------------------
    # Detailed NAV Trends for Drill-Through (all 40 funds)
    # We will compile downsampled daily/weekly NAV history for all 40 schemes to allow drill-through
    # ----------------------------------------------------
    all_schemes_nav_df = pd.read_sql_query("""
        SELECT n.amfi_code, n.date, n.nav
        FROM fact_nav n
        JOIN dim_date d ON n.date = d.date
        WHERE d.day_name = 'Friday' OR d.day = 1
        ORDER BY n.date ASC
    """, conn)
    
    # Group NAVs by amfi_code
    drill_through_navs = {}
    for amfi_code, group in all_schemes_nav_df.groupby('amfi_code'):
        drill_through_navs[int(amfi_code)] = {
            "dates": group['date'].tolist(),
            "navs": group['nav'].tolist()
        }

    # Compile everything into a single JS file
    payload = {
        "latest_date": latest_date,
        "kpis": {
            "total_aum_lakh_cr": total_aum_lakh_cr,
            "sip_inflow_crore": latest_sip_crore,
            "folios_crore": latest_folios_cr,
            "schemes_count": industry_schemes
        },
        "aum_trend": aum_trend,
        "aum_by_amc": aum_by_amc,
        "scatter_data": scatter_data,
        "scorecard_data": scorecard_data,
        "nav_history": nav_history,
        "state_trans": state_trans,
        "type_split": type_split,
        "age_sip": age_sip,
        "volume_trend": volume_trend,
        "sip_nifty": sip_nifty,
        "heatmap_data": heatmap_data,
        "top_categories_fy25": top_categories_fy25,
        "slicers": {
            "states": states_list,
            "age_groups": age_groups_list,
            "city_tiers": city_tiers_list
        },
        "drill_through_navs": drill_through_navs
    }
    
    # Save to file
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("const dashboardData = " + json.dumps(payload, cls=NpEncoder, indent=2) + ";")
        
    print(f"Successfully extracted data and wrote to {OUTPUT_PATH}")
    conn.close()

if __name__ == "__main__":
    extract_data()
