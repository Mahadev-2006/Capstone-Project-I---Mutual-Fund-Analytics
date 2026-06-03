import os
import pandas as pd
import numpy as np

# Path configurations
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"

def setup_directories():
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    print(f"Directory '{PROCESSED_DATA_DIR}' verified/created.")

def clean_fund_master():
    print("\n--- Cleaning 01_fund_master.csv ---")
    raw_path = os.path.join(RAW_DATA_DIR, "01_fund_master.csv")
    processed_path = os.path.join(PROCESSED_DATA_DIR, "01_fund_master.csv")
    
    df = pd.read_csv(raw_path)
    initial_shape = df.shape
    
    # 1. Clean string fields
    string_cols = df.select_dtypes(include=['object']).columns
    for col in string_cols:
        df[col] = df[col].astype(str).str.strip()
        
    # 2. Parse launch_date
    df['launch_date'] = pd.to_datetime(df['launch_date']).dt.strftime('%Y-%m-%d')
    
    # 3. Handle anomalies/missing values in exit load, expense ratio etc.
    # Check expense_ratio range (should be positive, mostly in % scale like 1.54)
    # Fill standard NaN representation for text if any
    df = df.dropna(subset=['amfi_code'])
    df['amfi_code'] = df['amfi_code'].astype(int)
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['amfi_code'])
    
    df.to_csv(processed_path, index=False)
    print(f"Fund Master cleaned. Initial shape: {initial_shape}, Final shape: {df.shape}")
    return df

def clean_nav_history(fund_master_df):
    print("\n--- Cleaning 02_nav_history.csv ---")
    raw_path = os.path.join(RAW_DATA_DIR, "02_nav_history.csv")
    processed_path = os.path.join(PROCESSED_DATA_DIR, "02_nav_history.csv")
    
    df = pd.read_csv(raw_path)
    initial_shape = df.shape
    
    # Remove duplicates immediately
    df = df.drop_duplicates()
    
    # Parse dates
    df['date'] = pd.to_datetime(df['date'])
    df['amfi_code'] = df['amfi_code'].astype(int)
    
    # Validate NAV > 0
    non_positive_count = (df['nav'] <= 0).sum()
    if non_positive_count > 0:
        print(f"  [WARNING] Dropping {non_positive_count} records where NAV <= 0.")
        df = df[df['nav'] > 0]
        
    # Drop rows where NAV is NaN
    df = df.dropna(subset=['nav'])
    
    # Forward-fill missing NAV for holidays/weekends
    # To do this per amfi_code, we find min and max date for each amfi_code,
    # generate a daily date range, reindex, and ffill
    filled_dfs = []
    unique_codes = df['amfi_code'].unique()
    
    for code in unique_codes:
        sub_df = df[df['amfi_code'] == code].copy()
        sub_df = sub_df.sort_values('date')
        
        min_date = sub_df['date'].min()
        max_date = sub_df['date'].max()
        
        # Generate complete daily date range
        daily_range = pd.date_range(start=min_date, end=max_date, freq='D')
        
        # Reindex
        sub_df = sub_df.set_index('date')
        sub_df = sub_df.reindex(daily_range)
        sub_df.index.name = 'date'
        
        # Track whether the record was filled
        sub_df['is_holiday_weekend_filled'] = sub_df['amfi_code'].isna().astype(int)
        
        # Fill identifier values
        sub_df['amfi_code'] = code
        
        # Forward fill NAV values
        sub_df['nav'] = sub_df['nav'].ffill()
        
        sub_df = sub_df.reset_index()
        filled_dfs.append(sub_df)
        
    final_df = pd.concat(filled_dfs, ignore_index=True)
    
    # Format date back to string YYYY-MM-DD
    final_df['date'] = final_df['date'].dt.strftime('%Y-%m-%d')
    final_df['amfi_code'] = final_df['amfi_code'].astype(int)
    final_df['is_holiday_weekend_filled'] = final_df['is_holiday_weekend_filled'].astype(int)
    
    # Sort
    final_df = final_df.sort_values(by=['amfi_code', 'date'])
    
    final_df.to_csv(processed_path, index=False)
    print(f"NAV History cleaned. Initial shape: {initial_shape}, Final shape: {final_df.shape}")
    print(f"  Holiday/weekend filled records: {final_df['is_holiday_weekend_filled'].sum()}")
    return final_df

def clean_aum_by_fund_house():
    print("\n--- Cleaning 03_aum_by_fund_house.csv ---")
    raw_path = os.path.join(RAW_DATA_DIR, "03_aum_by_fund_house.csv")
    processed_path = os.path.join(PROCESSED_DATA_DIR, "03_aum_by_fund_house.csv")
    
    df = pd.read_csv(raw_path)
    initial_shape = df.shape
    
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    df['fund_house'] = df['fund_house'].str.strip()
    df = df.drop_duplicates()
    
    df.to_csv(processed_path, index=False)
    print(f"AUM cleaned. Initial shape: {initial_shape}, Final shape: {df.shape}")
    return df

def clean_monthly_sip_inflows():
    print("\n--- Cleaning 04_monthly_sip_inflows.csv ---")
    raw_path = os.path.join(RAW_DATA_DIR, "04_monthly_sip_inflows.csv")
    processed_path = os.path.join(PROCESSED_DATA_DIR, "04_monthly_sip_inflows.csv")
    
    df = pd.read_csv(raw_path)
    initial_shape = df.shape
    
    # Parse month column to standard YYYY-MM
    df['month'] = pd.to_datetime(df['month'], format='%Y-%m').dt.strftime('%Y-%m')
    
    # Check missing yoy_growth_pct. Let's see if we can calculate it or leave it as null
    # If yoy_growth_pct is null, let's keep it null in the CSV but standardise its representation
    df = df.drop_duplicates()
    
    df.to_csv(processed_path, index=False)
    print(f"Monthly SIP Inflows cleaned. Initial shape: {initial_shape}, Final shape: {df.shape}")
    return df

def clean_category_inflows():
    print("\n--- Cleaning 05_category_inflows.csv ---")
    raw_path = os.path.join(RAW_DATA_DIR, "05_category_inflows.csv")
    processed_path = os.path.join(PROCESSED_DATA_DIR, "05_category_inflows.csv")
    
    df = pd.read_csv(raw_path)
    initial_shape = df.shape
    
    df['month'] = pd.to_datetime(df['month'], format='%Y-%m').dt.strftime('%Y-%m')
    df['category'] = df['category'].str.strip()
    df = df.drop_duplicates()
    
    df.to_csv(processed_path, index=False)
    print(f"Category Inflows cleaned. Initial shape: {initial_shape}, Final shape: {df.shape}")
    return df

def clean_industry_folio_count():
    print("\n--- Cleaning 06_industry_folio_count.csv ---")
    raw_path = os.path.join(RAW_DATA_DIR, "06_industry_folio_count.csv")
    processed_path = os.path.join(PROCESSED_DATA_DIR, "06_industry_folio_count.csv")
    
    df = pd.read_csv(raw_path)
    initial_shape = df.shape
    
    df['month'] = pd.to_datetime(df['month'], format='%Y-%m').dt.strftime('%Y-%m')
    df = df.drop_duplicates()
    
    df.to_csv(processed_path, index=False)
    print(f"Folio Count cleaned. Initial shape: {initial_shape}, Final shape: {df.shape}")
    return df

def clean_scheme_performance():
    print("\n--- Cleaning 07_scheme_performance.csv ---")
    raw_path = os.path.join(RAW_DATA_DIR, "07_scheme_performance.csv")
    processed_path = os.path.join(PROCESSED_DATA_DIR, "07_scheme_performance.csv")
    
    df = pd.read_csv(raw_path)
    initial_shape = df.shape
    
    # 1. Clean string fields
    for col in ['scheme_name', 'fund_house', 'category', 'plan', 'risk_grade']:
        df[col] = df[col].astype(str).str.strip()
        
    # 2. Validate return columns are numeric
    return_cols = ['return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct', 'alpha', 'beta', 'sharpe_ratio', 'sortino_ratio', 'std_dev_ann_pct', 'max_drawdown_pct']
    for col in return_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # 3. Check expense_ratio range (0.1% – 2.5%) and log anomalies
    df['expense_ratio_pct'] = pd.to_numeric(df['expense_ratio_pct'], errors='coerce')
    out_of_bounds = df[(df['expense_ratio_pct'] < 0.1) | (df['expense_ratio_pct'] > 2.5)]
    if not out_of_bounds.empty:
        print(f"  [ANOMALY] {len(out_of_bounds)} funds have expense ratio out of [0.1%, 2.5%] bounds:")
        for idx, row in out_of_bounds.iterrows():
            print(f"    - AMFI: {row['amfi_code']}, Fund: {row['scheme_name']}, Expense Ratio: {row['expense_ratio_pct']}%")
            
    # Add an anomaly flag column for our processed CSV so analytical queries can inspect it
    df['is_expense_ratio_anomalous'] = ((df['expense_ratio_pct'] < 0.1) | (df['expense_ratio_pct'] > 2.5)).astype(int)
    
    # Check for drawdown anomalies (e.g. if positive, make negative if standard representation requires it,
    # but in our previous data summary we saw drawdown was negative -33.5 which is logical for losses)
    # Let's keep it as is, but ensure it is numeric.
    
    df = df.drop_duplicates(subset=['amfi_code'])
    df['amfi_code'] = df['amfi_code'].astype(int)
    
    df.to_csv(processed_path, index=False)
    print(f"Scheme Performance cleaned. Initial shape: {initial_shape}, Final shape: {df.shape}")
    return df

def clean_investor_transactions():
    print("\n--- Cleaning 08_investor_transactions.csv ---")
    raw_path = os.path.join(RAW_DATA_DIR, "08_investor_transactions.csv")
    processed_path = os.path.join(PROCESSED_DATA_DIR, "08_investor_transactions.csv")
    
    df = pd.read_csv(raw_path)
    initial_shape = df.shape
    
    # 1. Standardise transaction_type values
    # Let's see unique values first, strip whitespace and make them uniform
    df['transaction_type'] = df['transaction_type'].astype(str).str.strip()
    # E.g. make sure SIP, Lumpsum, Redemption are the only ones
    type_mapping = {
        'sip': 'SIP', 'SIP': 'SIP',
        'lumpsum': 'Lumpsum', 'Lumpsum': 'Lumpsum',
        'redemption': 'Redemption', 'Redemption': 'Redemption'
    }
    df['transaction_type'] = df['transaction_type'].map(lambda x: type_mapping.get(x, x.title()))
    
    # 2. Validate amount > 0
    non_positive_count = (df['amount_inr'] <= 0).sum()
    if non_positive_count > 0:
        print(f"  [WARNING] Dropping {non_positive_count} transactions where amount <= 0.")
        df = df[df['amount_inr'] > 0]
        
    # 3. Fix date formats
    df['transaction_date'] = pd.to_datetime(df['transaction_date']).dt.strftime('%Y-%m-%d')
    
    # 4. Check KYC status enum values
    df['kyc_status'] = df['kyc_status'].astype(str).str.strip().str.capitalize()
    # Map to Verified / Pending
    df['kyc_status'] = df['kyc_status'].replace({'Pending': 'Pending', 'Verified': 'Verified'})
    
    # Clean standard string columns
    for col in ['investor_id', 'state', 'city', 'city_tier', 'age_group', 'gender', 'payment_mode']:
        df[col] = df[col].astype(str).str.strip()
        
    df['amfi_code'] = df['amfi_code'].astype(int)
    
    df = df.drop_duplicates()
    df.to_csv(processed_path, index=False)
    print(f"Investor Transactions cleaned. Initial shape: {initial_shape}, Final shape: {df.shape}")
    return df

def clean_portfolio_holdings():
    print("\n--- Cleaning 09_portfolio_holdings.csv ---")
    raw_path = os.path.join(RAW_DATA_DIR, "09_portfolio_holdings.csv")
    processed_path = os.path.join(PROCESSED_DATA_DIR, "09_portfolio_holdings.csv")
    
    df = pd.read_csv(raw_path)
    initial_shape = df.shape
    
    df['portfolio_date'] = pd.to_datetime(df['portfolio_date']).dt.strftime('%Y-%m-%d')
    
    for col in ['stock_symbol', 'stock_name', 'sector']:
        df[col] = df[col].astype(str).str.strip()
        
    df['amfi_code'] = df['amfi_code'].astype(int)
    df = df.drop_duplicates()
    
    df.to_csv(processed_path, index=False)
    print(f"Portfolio Holdings cleaned. Initial shape: {initial_shape}, Final shape: {df.shape}")
    return df

def clean_benchmark_indices():
    print("\n--- Cleaning 10_benchmark_indices.csv ---")
    raw_path = os.path.join(RAW_DATA_DIR, "10_benchmark_indices.csv")
    processed_path = os.path.join(PROCESSED_DATA_DIR, "10_benchmark_indices.csv")
    
    df = pd.read_csv(raw_path)
    initial_shape = df.shape
    
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    df['index_name'] = df['index_name'].astype(str).str.strip()
    df = df.drop_duplicates()
    
    df.to_csv(processed_path, index=False)
    print(f"Benchmark Indices cleaned. Initial shape: {initial_shape}, Final shape: {df.shape}")
    return df

def main():
    print("==================================================")
    print("Mutual Fund Data Cleaning Pipeline (Day 2)")
    print("==================================================")
    setup_directories()
    
    fund_master = clean_fund_master()
    clean_nav_history(fund_master)
    clean_aum_by_fund_house()
    clean_monthly_sip_inflows()
    clean_category_inflows()
    clean_industry_folio_count()
    clean_scheme_performance()
    clean_investor_transactions()
    clean_portfolio_holdings()
    clean_benchmark_indices()
    
    print("\n==================================================")
    print("Data cleaning completed successfully.")
    print("All 10 cleaned CSV files saved in data/processed/")
    print("==================================================")

if __name__ == "__main__":
    main()
