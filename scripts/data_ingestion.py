import os
import pandas as pd
import numpy as np

# Directory constants
DATA_DIR = "data/raw"
REPORTS_DIR = "reports"

# File name mapping for 10 datasets
DATASETS = {
    "01_fund_master.csv": "Fund Master",
    "02_nav_history.csv": "NAV History",
    "03_aum_by_fund_house.csv": "AUM by Fund House",
    "04_monthly_sip_inflows.csv": "Monthly SIP Inflows",
    "05_category_inflows.csv": "Category Inflows",
    "06_industry_folio_count.csv": "Industry Folio Count",
    "07_scheme_performance.csv": "Scheme Performance",
    "08_investor_transactions.csv": "Investor Transactions",
    "09_portfolio_holdings.csv": "Portfolio Holdings",
    "10_benchmark_indices.csv": "Benchmark Indices"
}

def check_anomalies(df, filename):
    anomalies = []
    
    # 1. Check for missing values
    missing_counts = df.isnull().sum()
    cols_with_missing = missing_counts[missing_counts > 0]
    if not cols_with_missing.empty:
        for col, count in cols_with_missing.items():
            pct = (count / len(df)) * 100
            anomalies.append(f"Missing Values: Column '{col}' has {count} nulls ({pct:.2f}%)")
            
    # 2. Check for duplicate rows
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        anomalies.append(f"Duplicates: {duplicate_count} fully duplicated rows found.")
        
    # 3. Check for specific numeric anomalies (e.g. negative values in typical positive columns)
    for col in df.select_dtypes(include=[np.number]).columns:
        # Avoid checking code columns or transaction IDs
        if "code" in col.lower() or "id" in col.lower():
            continue
        min_val = df[col].min()
        if min_val < 0:
            anomalies.append(f"Negative Values: Column '{col}' contains negative values (Min: {min_val})")
            
    return anomalies

def load_and_inspect_datasets():
    loaded_dfs = {}
    dataset_reports = []
    
    print("==================================================")
    print("Step 1: Loading and Inspecting 10 CSV Datasets")
    print("==================================================")
    
    for filename, display_name in DATASETS.items():
        filepath = os.path.join(DATA_DIR, filename)
        print(f"\n--- Loading {display_name} ({filename}) ---")
        
        if not os.path.exists(filepath):
            print(f"Error: File {filepath} not found!")
            continue
            
        try:
            df = pd.read_csv(filepath)
            loaded_dfs[filename] = df
            
            # Print basic info
            print(f"Shape: {df.shape}")
            print("\nData Types:")
            print(df.dtypes)
            print("\nFirst 3 rows:")
            print(df.head(3))
            
            # Check for anomalies
            anomalies = check_anomalies(df, filename)
            if anomalies:
                print("\n[ANOMALY] Anomalies detected:")
                for anomaly in anomalies:
                    print(f"  - {anomaly}")
            else:
                print("\n[OK] No simple anomalies detected.")
                
            dataset_reports.append({
                "filename": filename,
                "name": display_name,
                "shape": df.shape,
                "columns": list(df.columns),
                "anomalies": anomalies
            })
            
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            
    return loaded_dfs, dataset_reports

def explore_fund_master(df):
    print("\n==================================================")
    print("Step 2: Exploring Fund Master")
    print("==================================================")
    
    if df is None:
        print("Fund Master dataset not available.")
        return {}
        
    unique_houses = df["fund_house"].dropna().unique()
    unique_categories = df["category"].dropna().unique()
    unique_subcategories = df["sub_category"].dropna().unique()
    unique_risk_grades = df["risk_category"].dropna().unique()
    
    print(f"Unique Fund Houses ({len(unique_houses)}):")
    print(", ".join(unique_houses))
    
    print(f"\nUnique Categories ({len(unique_categories)}):")
    print(", ".join(unique_categories))
    
    print(f"\nUnique Sub-Categories ({len(unique_subcategories)}):")
    print(", ".join(unique_subcategories))
    
    print(f"\nUnique Risk Categories ({len(unique_risk_grades)}):")
    print(", ".join(unique_risk_grades))
    
    print("\nAMFI Scheme Code Structure:")
    print("- AMFI code is a unique numeric identifier (e.g. 119551) assigned to each mutual fund scheme by AMFI (Association of Mutual Funds in India).")
    print("- Under a specific scheme (like SBI Bluechip Fund), regular and direct plans have distinct AMFI codes (e.g., 119551 for Regular, 119552 for Direct).")
    print("- It serves as a foreign key that connects the static fund metadata to date-wise NAV values, holdings, and transaction records.")
    
    return {
        "fund_houses": list(unique_houses),
        "categories": list(unique_categories),
        "sub_categories": list(unique_subcategories),
        "risk_categories": list(unique_risk_grades)
    }

def validate_amfi_codes(fund_master_df, nav_history_df):
    print("\n==================================================")
    print("Step 3: Validating AMFI Codes")
    print("==================================================")
    
    if fund_master_df is None or nav_history_df is None:
        print("Required datasets for validation are not available.")
        return None
        
    master_codes = set(fund_master_df["amfi_code"].unique())
    history_codes = set(nav_history_df["amfi_code"].unique())
    
    total_master = len(master_codes)
    total_history = len(history_codes)
    
    intersection = master_codes.intersection(history_codes)
    missing_in_history = master_codes - history_codes
    extra_in_history = history_codes - master_codes
    
    print(f"Total unique AMFI codes in Fund Master: {total_master}")
    print(f"Total unique AMFI codes in NAV History: {total_history}")
    print(f"Matching codes in both datasets: {len(intersection)} ({(len(intersection)/total_master)*100:.2f}% of Master)")
    
    if missing_in_history:
        print(f"[WARNING] Codes in Fund Master but MISSING in NAV History ({len(missing_in_history)}):")
        print(missing_in_history)
    else:
        print("[OK] Excellent: Every AMFI code in Fund Master exists in NAV History.")
        
    if extra_in_history:
        print(f"[INFO] Codes in NAV History but NOT in Fund Master ({len(extra_in_history)}):")
        print(f"Sample of extra codes: {list(extra_in_history)[:10]}...")
        
    return {
        "total_master_codes": total_master,
        "total_history_codes": total_history,
        "matching_codes": len(intersection),
        "missing_in_history": list(missing_in_history),
        "extra_in_history": list(extra_in_history)
    }

def write_data_quality_report(dataset_reports, master_exploration, validation_results):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, "data_quality_summary.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Data Quality & Ingestion Summary - Day 1\n\n")
        f.write("This report provides an automated data quality summary for the loaded Mutual Fund datasets.\n\n")
        
        f.write("## 1. Datasets Ingested\n\n")
        f.write("| File Name | Display Name | Rows | Columns | Status |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        
        for r in dataset_reports:
            status = "✅ Clean" if not r["anomalies"] else "⚠️ Anomalies Detected"
            f.write(f"| {r['filename']} | {r['name']} | {r['shape'][0]:,} | {r['shape'][1]} | {status} |\n")
            
        f.write("\n## 2. In-Depth Dataset Anomalies\n\n")
        any_anomalies = False
        for r in dataset_reports:
            if r["anomalies"]:
                any_anomalies = True
                f.write(f"### {r['name']} (`{r['filename']}`)\n")
                for a in r["anomalies"]:
                    f.write(f"- {a}\n")
                f.write("\n")
        if not any_anomalies:
            f.write("No major anomalies were detected in any of the 10 datasets.\n\n")
            
        f.write("## 3. Fund Master Dimensions\n\n")
        if master_exploration:
            f.write(f"- **Unique Fund Houses ({len(master_exploration['fund_houses'])}):** {', '.join(master_exploration['fund_houses'])}\n")
            f.write(f"- **Unique Categories ({len(master_exploration['categories'])}):** {', '.join(master_exploration['categories'])}\n")
            f.write(f"- **Unique Sub-Categories ({len(master_exploration['sub_categories'])}):** {', '.join(master_exploration['sub_categories'])}\n")
            f.write(f"- **Unique Risk Categories ({len(master_exploration['risk_categories'])}):** {', '.join(master_exploration['risk_categories'])}\n\n")
            
        f.write("## 4. AMFI Code Validation Results\n\n")
        if validation_results:
            f.write(f"- **Unique Codes in Fund Master:** {validation_results['total_master_codes']}\n")
            f.write(f"- **Unique Codes in NAV History:** {validation_results['total_history_codes']}\n")
            f.write(f"- **Matching Codes:** {validation_results['matching_codes']} / {validation_results['total_master_codes']} ({(validation_results['matching_codes']/validation_results['total_master_codes'])*100:.2f}%)\n")
            
            missing_cnt = len(validation_results['missing_in_history'])
            if missing_cnt > 0:
                f.write(f"\n### ⚠️ Missing Codes ({missing_cnt})\n")
                f.write("The following AMFI codes are defined in the Fund Master but lack any records in NAV History:\n")
                f.write(", ".join(map(str, validation_results['missing_in_history'])) + "\n")
            else:
                f.write("\n✅ **Data Integrity Check Passed:** All codes defined in the Fund Master are successfully mapped in the NAV History.\n")
                
            extra_cnt = len(validation_results['extra_in_history'])
            if extra_cnt > 0:
                f.write(f"\n### ℹ️ Extra Codes in History ({extra_cnt})\n")
                f.write(f"There are {extra_cnt} AMFI codes present in the NAV History that are not registered in the Fund Master. This indicates the historical data contains additional schemes not currently configured in metadata.\n")
                
    print(f"\nData quality summary report successfully saved to: {report_path}")

def main():
    dfs, dataset_reports = load_and_inspect_datasets()
    
    fund_master_df = dfs.get("01_fund_master.csv")
    nav_history_df = dfs.get("02_nav_history.csv")
    
    master_exploration = explore_fund_master(fund_master_df)
    validation_results = validate_amfi_codes(fund_master_df, nav_history_df)
    
    write_data_quality_report(dataset_reports, master_exploration, validation_results)

if __name__ == "__main__":
    main()
