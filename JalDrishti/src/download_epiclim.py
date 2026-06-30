"""Download epiclim_raw.csv from Zenodo."""
import requests
from pathlib import Path

OUT = Path(__file__).parent.parent / "data/raw/epiclim_raw.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

print("Fetching Zenodo record metadata...")
r = requests.get("https://zenodo.org/api/records/14580510", timeout=30)
r.raise_for_status()
files = r.json().get("files", [])
csv_url = next((f["links"]["self"] for f in files if f.get("key","").endswith(".csv")), None)
if not csv_url:
    raise RuntimeError("No CSV found in Zenodo record 14580510")

print(f"Downloading from {csv_url[:60]}...")
r2 = requests.get(csv_url, timeout=180, stream=True)
r2.raise_for_status()
with open(OUT, "wb") as fh:
    total = 0
    for chunk in r2.iter_content(8192):
        fh.write(chunk)
        total += len(chunk)
print(f"Saved {total:,} bytes -> {OUT}")
print("PASS")
