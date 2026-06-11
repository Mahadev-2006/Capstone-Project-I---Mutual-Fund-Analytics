import os
import sys
import subprocess
import time

PYTHON_EXE = os.path.join(".venv", "Scripts", "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = "python"  # Fallback to system python

def run_script(script_path, desc):
    print("\n" + "="*80)
    print(f" PIPELINE STEP: {desc.upper()}")
    print(f" Executing: {PYTHON_EXE} {script_path}")
    print("="*80)
    
    start_time = time.time()
    
    # Run subprocess
    result = subprocess.run([PYTHON_EXE, script_path], capture_output=False)
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    if result.returncode == 0:
        print(f"SUCCESS: {desc} completed successfully in {elapsed:.2f} seconds.")
    else:
        print(f"ERROR: {desc} failed with exit code {result.returncode} after {elapsed:.2f} seconds.")
        sys.exit(result.returncode)

def main():
    print("="*80)
    print(" BLUESTOCK MUTUAL FUND ANALYTICS - MASTER PIPELINE EXECUTION")
    print("="*80)
    
    pipeline_start = time.time()
    
    # Verify environment
    if not os.path.exists(".venv"):
        print("Warning: Virtual environment '.venv' not found. Running with default Python interpreter.")
        
    # Step 1: Data Ingestion & Cleaning
    run_script("scripts/data_cleaning.py", "Data Cleaning and Processing")
    
    # Step 2: DB Loader (Star Schema mapping)
    run_script("scripts/db_loader.py", "SQLite Database Ingestion")
    
    # Step 3: Performance Quantitative Analytics (Day 4)
    run_script("scripts/generate_analytics.py", "Performance Analytics (Day 4)")
    
    # Step 4: Advanced Behavioral & Risk Analytics (Day 6)
    run_script("scripts/generate_advanced_analytics.py", "Advanced Financial Analytics (Day 6)")
    
    # Step 5: Dashboard Data Export
    run_script("scripts/extract_dashboard_data.py", "Web Dashboard Data Export")
    
    # Step 6: Automated Dashboard Report Generation (Screenshots + PDF + PBIX)
    run_script("scripts/generate_report.py", "Dashboard Screenshot & PDF Generation")
    
    pipeline_end = time.time()
    total_elapsed = pipeline_end - pipeline_start
    
    print("\n" + "="*80)
    print(" MASTER PIPELINE COMPLETED SUCCESSFULLY!")
    print(f" Total Execution Time: {total_elapsed:.2f} seconds ({total_elapsed/60:.2f} minutes)")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
