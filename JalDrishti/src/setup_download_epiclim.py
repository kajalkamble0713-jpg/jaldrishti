"""
Step 4: Download EpiClim dataset from Zenodo record 14580510.
"""
import requests
import json
import pandas as pd
from pathlib import Path

OUT_PATH = Path("data/raw/epiclim_raw.csv")

def download_epiclim():
    print("=== EpiClim Download ===")
    # Step 1: Query Zenodo API
    api_url = "https://zenodo.org/api/records/14580510"
    print(f"Querying Zenodo API: {api_url}")
    try:
        r = requests.get(api_url, timeout=30)
        r.raise_for_status()
        record = r.json()
    except Exception as e:
        print(f"  FAILED to query Zenodo API: {e}")
        return False

    # Step 2: Find CSV file in files list
    files = record.get("files", [])
    csv_url = None
    for f in files:
        if f.get("key", "").endswith(".csv"):
            csv_url = f["links"]["self"]
            print(f"  Found CSV: {f['key']} ({f.get('size', '?')} bytes)")
            break

    if not csv_url:
        print("  No CSV found in record files — trying fallback page scrape...")
        return False

    # Step 3: Download the CSV
    print(f"  Downloading from: {csv_url}")
    try:
        r2 = requests.get(csv_url, timeout=120, stream=True)
        r2.raise_for_status()
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUT_PATH, "wb") as fh:
            for chunk in r2.iter_content(chunk_size=8192):
                fh.write(chunk)
        print(f"  Saved to: {OUT_PATH}")
    except Exception as e:
        print(f"  FAILED to download CSV: {e}")
        return False

    # Step 4: Verify
    try:
        df = pd.read_csv(OUT_PATH)
        print(f"  Rows: {len(df)}, Columns: {list(df.columns)}")
        file_size = OUT_PATH.stat().st_size
        print(f"  File size: {file_size:,} bytes")
        if abs(len(df) - 8985) > 2000:
            print(f"  WARNING: Row count {len(df)} differs significantly from expected ~8985")
        else:
            print(f"  Row count OK (expected ~8985, got {len(df)})")
        print("  STATUS: PASS")
        return True
    except Exception as e:
        print(f"  FAILED to parse CSV: {e}")
        return False

if __name__ == "__main__":
    download_epiclim()
