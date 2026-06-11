import os
import sys
import sqlite3
import argparse

DB_PATH = "bluestock_mf.db"

def get_recommendations(risk_appetite):
    # Normalize risk appetite input
    risk_appetite = risk_appetite.strip().capitalize()
    
    # Map risk appetite to database risk_grade values
    risk_mapping = {
        "Low": ["Low"],
        "Moderate": ["Moderate", "Moderately High"],
        "High": ["High", "Very High"]
    }
    
    if risk_appetite not in risk_mapping:
        print(f"Error: Invalid risk appetite '{risk_appetite}'. Must be one of: Low, Moderate, High.")
        sys.exit(1)
        
    grades = risk_mapping[risk_appetite]
    
    # Handle DB path context
    db_file = DB_PATH
    if not os.path.exists(db_file):
        # Check parent folder or dynamic paths
        if os.path.exists("../bluestock_mf.db"):
            db_file = "../bluestock_mf.db"
        else:
            print("Error: Database file 'bluestock_mf.db' not found in the workspace.")
            sys.exit(1)
            
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Construct IN query
    placeholders = ",".join(["?"] * len(grades))
    query = f"""
        SELECT f.scheme_name, f.category, p.risk_grade, p.sharpe_ratio, p.return_3yr_pct, f.fund_house
        FROM dim_fund f
        JOIN fact_performance p ON f.amfi_code = p.amfi_code
        WHERE p.risk_grade IN ({placeholders})
        ORDER BY p.sharpe_ratio DESC
        LIMIT 3
    """
    
    cursor.execute(query, grades)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print(f"No funds found matching risk grades: {', '.join(grades)}")
        return
        
    print("\n" + "="*80)
    print(f" BLUESTOCK MUTUAL FUND RECOMMENDER - RISK APPETITE: {risk_appetite.upper()}")
    print(f" Recommending top 3 funds by Sharpe ratio within matching risk grades ({', '.join(grades)}):")
    print("="*80)
    
    # Print header
    print(f"{'Rank':<5} | {'Scheme Name':<45} | {'Category':<10} | {'Sharpe':<8} | {'3Y Ret':<8}")
    print("-"*80)
    
    for idx, row in enumerate(rows, 1):
        name = row[0]
        # Shorten name if too long for tabular print
        if len(name) > 42:
            name = name[:42] + "..."
        category = row[1]
        risk_grade = row[2]
        sharpe = row[3]
        return_3y = row[4]
        
        print(f"{idx:<5} | {name:<45} | {category:<10} | {sharpe:<8.3f} | {return_3y:<7.2f}%")
    print("="*80 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Bluestock Mutual Fund Recommender")
    parser.add_argument(
        "-r", "--risk", 
        type=str, 
        choices=["Low", "Moderate", "High", "low", "moderate", "high"],
        help="Risk appetite (Low, Moderate, High)"
    )
    
    args = parser.parse_args()
    
    if args.risk:
        get_recommendations(args.risk)
    else:
        # Interactive mode
        print("Welcome to the Bluestock Mutual Fund Recommender Tool!")
        try:
            val = input("Enter your risk appetite (Low / Moderate / High): ")
            get_recommendations(val)
        except KeyboardInterrupt:
            print("\nExiting recommender.")
            sys.exit(0)

if __name__ == "__main__":
    main()
