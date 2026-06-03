import os
import requests
import pandas as pd

# Constants
API_BASE_URL = "https://api.mfapi.in/mf"
DATA_DIR = "data/raw"

# Target schemes
SCHEMES = {
    "125497": "HDFC Top 100 Fund - Direct Plan - Growth",
    "119551": "SBI Bluechip Fund - Regular Plan - Growth",
    "120503": "ICICI Pru Bluechip Fund - Regular - Growth",
    "118632": "Nippon India Large Cap Fund - Regular - Growth",
    "119092": "Axis Bluechip Fund - Regular - Growth",
    "120841": "Kotak Bluechip Fund - Regular - Growth"
}

def fetch_and_save_nav(scheme_code, scheme_name):
    print(f"Fetching NAV data for scheme {scheme_code} ({scheme_name})...")
    url = f"{API_BASE_URL}/{scheme_code}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        json_data = response.json()
        
        if not json_data or "data" not in json_data or "meta" not in json_data:
            print(f"Error: Invalid or empty response from API for scheme {scheme_code}.")
            return False
            
        meta = json_data["meta"]
        nav_list = json_data["data"]
        
        # Convert to DataFrame
        df = pd.DataFrame(nav_list)
        
        # Add metadata columns
        df["scheme_code"] = scheme_code
        df["scheme_name"] = meta.get("scheme_name", scheme_name)
        df["fund_house"] = meta.get("fund_house", "Unknown")
        
        # Reorder columns for readability
        df = df[["scheme_code", "scheme_name", "fund_house", "date", "nav"]]
        
        # Ensure output directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Save to CSV
        output_path = os.path.join(DATA_DIR, f"live_nav_{scheme_code}.csv")
        df.to_csv(output_path, index=False)
        
        # Get latest NAV details (typically the first element in the list is the latest, but let's be sure by peaking)
        if not df.empty:
            latest_record = df.iloc[0]
            print(f"Success! Saved {len(df)} records to {output_path}")
            print(f"  Latest NAV Date: {latest_record['date']}, NAV: {latest_record['nav']}")
        else:
            print(f"Warning: Fetched data is empty for scheme {scheme_code}.")
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"HTTP Error fetching data for scheme {scheme_code}: {e}")
    except ValueError as e:
        print(f"JSON Parsing Error for scheme {scheme_code}: {e}")
    except Exception as e:
        print(f"Unexpected Error for scheme {scheme_code}: {e}")
        
    return False

def main():
    print("==================================================")
    print("MF Live NAV Fetcher (mfapi.in)")
    print("==================================================")
    
    success_count = 0
    for code, name in SCHEMES.items():
        if fetch_and_save_nav(code, name):
            success_count += 1
        print("-" * 50)
        
    print(f"Fetch completed. Successfully processed {success_count}/{len(SCHEMES)} schemes.")

if __name__ == "__main__":
    main()
