import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

# Configuration
PROCESSED_DIR = "data/processed"
DB_PATH = "bluestock_mf.db"
SCHEMA_PATH = "sql/schema.sql"
QUERIES_PATH = "sql/queries.sql"
REPORTS_DIR = "reports"

# Mappings of Processed CSV -> DB Table
TABLE_MAPPINGS = {
    "01_fund_master.csv": "dim_fund",
    "02_nav_history.csv": "fact_nav",
    "03_aum_by_fund_house.csv": "fact_aum",
    "04_monthly_sip_inflows.csv": "fact_sip_inflows",
    "05_category_inflows.csv": "fact_category_inflows",
    "06_industry_folio_count.csv": "fact_folio_count",
    "07_scheme_performance.csv": "fact_performance",
    "08_investor_transactions.csv": "fact_transactions",
    "09_portfolio_holdings.csv": "fact_holdings",
    "10_benchmark_indices.csv": "fact_benchmark"
}

def create_database_and_schema():
    print("Creating database and running DDL schema...")
    # Delete old database if exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("  Removed existing database file.")
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Read schema SQL
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        
    # Execute DDL
    # Note: SQLite executescript allows multiple commands separated by semicolons
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()
    print("  Database tables and index definitions initialized successfully.")

def generate_and_load_calendar(engine):
    print("\nGenerating and loading dim_date calendar dimension...")
    # Create complete list of dates from 2022-01-01 to 2026-12-31
    date_range = pd.date_range(start="2022-01-01", end="2026-12-31", freq="D")
    
    dim_date_df = pd.DataFrame()
    dim_date_df["date"] = date_range.strftime("%Y-%m-%d")
    dim_date_df["year"] = date_range.year
    dim_date_df["month"] = date_range.month
    dim_date_df["day"] = date_range.day
    dim_date_df["quarter"] = date_range.quarter
    dim_date_df["is_weekend"] = date_range.weekday.map(lambda x: 1 if x in (5, 6) else 0)
    dim_date_df["month_name"] = date_range.strftime("%B")
    dim_date_df["day_name"] = date_range.strftime("%A")
    
    # Write to SQL
    dim_date_df.to_sql("dim_date", engine, if_exists="append", index=False)
    print(f"  Generated {len(dim_date_df)} calendar date rows loaded into SQLite 'dim_date'.")

def load_data_and_verify(engine):
    print("\nLoading cleaned datasets into database fact and dimension tables...")
    verification_results = []
    
    # Load dim_fund first because of foreign key references!
    # Order: dim_fund, then everything else
    ordered_files = [
        "01_fund_master.csv",
        "02_nav_history.csv",
        "03_aum_by_fund_house.csv",
        "04_monthly_sip_inflows.csv",
        "05_category_inflows.csv",
        "06_industry_folio_count.csv",
        "07_scheme_performance.csv",
        "08_investor_transactions.csv",
        "09_portfolio_holdings.csv",
        "10_benchmark_indices.csv"
    ]
    
    for filename in ordered_files:
        table_name = TABLE_MAPPINGS[filename]
        filepath = os.path.join(PROCESSED_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"  [ERROR] Cleaned file '{filepath}' not found!")
            continue
            
        df = pd.read_csv(filepath)
        csv_row_count = len(df)
        
        # Query existing database columns for this table using PRAGMA table_info
        with engine.connect() as conn:
            columns_info = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            db_columns = [col[1] for col in columns_info]
            
        # Filter dataframe to only include columns that exist in the database table
        if db_columns:
            # We intersect columns in df with columns in db, keeping df's ordering or matching exactly
            df_cols_to_keep = [col for col in df.columns if col in db_columns]
            df = df[df_cols_to_keep]
        
        # Append data to pre-defined tables
        df.to_sql(table_name, engine, if_exists="append", index=False)
        
        # Query count from SQL database to verify
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            db_row_count = result.scalar()
            
        status = "PASS" if csv_row_count == db_row_count else "FAIL"
        verification_results.append({
            "table": table_name,
            "csv_rows": csv_row_count,
            "db_rows": db_row_count,
            "status": status
        })
        print(f"  Loaded table '{table_name}': CSV rows = {csv_row_count}, DB rows = {db_row_count} ({status})")
        
    return verification_results

def run_analytical_queries(engine):
    print("\nRunning 10 analytical SQL queries on SQLite database...")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_output_path = os.path.join(REPORTS_DIR, "analytical_queries_output.txt")
    
    # Read queries
    with open(QUERIES_PATH, "r", encoding="utf-8") as f:
        queries_sql = f.read()
        
    # Split queries by semicolon (ignoring comments)
    queries = []
    current_query = []
    
    for line in queries_sql.split("\n"):
        clean_line = line.strip()
        # Skip PRAGMA lines
        if clean_line.startswith("PRAGMA"):
            continue
        current_query.append(line)
        if clean_line.endswith(";"):
            queries.append("\n".join(current_query))
            current_query = []
            
    # Clean up empty queries
    queries = [q.strip() for q in queries if q.strip()]
    
    with open(report_output_path, "w", encoding="utf-8") as report_file:
        report_file.write("==================================================\n")
        report_file.write("BLUESTOCK MUTUAL FUND ANALYTICS - DAY 2 QUERY OUTPUT\n")
        report_file.write("==================================================\n\n")
        
        for i, q in enumerate(queries, 1):
            title = f"Query {i}"
            # Extract query title from comments if possible
            for line in q.split("\n"):
                if line.strip().startswith("--"):
                    title = f"Query {i}: {line.replace('--', '').strip()}"
                    break
            
            print(f"  Executing {title}...")
            report_file.write(f"--- {title} ---\n")
            report_file.write(f"SQL Code:\n{q}\n\n")
            
            try:
                # Use pandas to read and format SQL results
                with engine.connect() as conn:
                    df = pd.read_sql(q, conn)
                
                # Format output
                result_str = df.to_string(index=False)
                report_file.write("Result:\n")
                report_file.write(result_str)
                report_file.write("\n\n" + "="*50 + "\n\n")
                
            except Exception as e:
                report_file.write(f"Execution Error: {e}\n\n" + "="*50 + "\n\n")
                print(f"    [ERROR] Failed to run {title}: {e}")
                
    print(f"  All SQL query execution outputs saved to: {report_output_path}")

def main():
    print("==================================================")
    print("Bluestock SQLite Loader Pipeline (Day 2)")
    print("==================================================")
    
    # Initialize SQLite SQLAlchemy Engine
    engine = create_engine(f"sqlite:///{DB_PATH}")
    
    # 1. Create database structure and schema
    create_database_and_schema()
    
    # 2. Generate dim_date rows
    generate_and_load_calendar(engine)
    
    # 3. Load all cleaned CSV datasets and verify row counts
    load_data_and_verify(engine)
    
    # 4. Run analytical queries and write report output
    run_analytical_queries(engine)
    
    print("\n==================================================")
    print("SQLite loading and analysis completed successfully.")
    print("==================================================")

if __name__ == "__main__":
    main()
