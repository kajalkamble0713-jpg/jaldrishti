"""
Phase 2 Step 4 — Build Simplified SVI
Usage: python src/build_svi.py
Output: data/processed/svi_scores_v2.csv
NOTE: This uses the existing SVI scores from the JalDrishti pipeline (already computed
      using PCA over 15 Census/NFHS indicators). If those don't exist, builds a proxy
      SVI from lat/lon-based urbanization proxy.
"""
import pandas as pd, numpy as np
from pathlib import Path

BASE = Path(__file__).parent.parent
EXISTING_SVI = BASE / "data/processed/district_svi_scores.csv"
CENTROIDS    = BASE / "data/geo/district_centroids.csv"
OUT          = BASE / "data/processed/svi_scores_v2.csv"

print("=== build_svi.py ===")

if EXISTING_SVI.exists():
    df = pd.read_csv(EXISTING_SVI)
    print(f"Using existing SVI from JalDrishti pipeline: {len(df):,} districts")
    print(f"Columns: {list(df.columns)}")
    print(f"SVI range: {df['svi_score'].min():.3f} - {df['svi_score'].max():.3f}")
    # Standardise column names
    df = df[["district_name","state_name","svi_score"]].copy()
    df["district_clean"] = df["district_name"].str.strip().str.upper()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Output: {len(df):,} rows -> {OUT}")
    print("PASS: svi_scores_v2.csv written (from existing pipeline)")
else:
    print("WARN: No existing SVI found. Building proxy SVI from centroids...")
    if not CENTROIDS.exists():
        print("FAIL: No centroids file either. Run prepare_geo.py first.")
        raise SystemExit(1)
    ctr = pd.read_csv(CENTROIDS)
    # Proxy SVI: normalize lat/lon distance from major urban centres
    # Higher distance from urban centres → higher vulnerability (simplified assumption)
    urban_centres = [(28.6, 77.2), (19.0, 72.8), (13.0, 80.2), (22.5, 88.3), (17.4, 78.5)]
    def min_dist(row):
        return min(((row.lat-uc[0])**2 + (row.lon-uc[1])**2)**0.5 for uc in urban_centres)
    ctr["raw_dist"] = ctr.apply(min_dist, axis=1)
    ctr["svi_score"] = (ctr["raw_dist"] - ctr["raw_dist"].min()) / \
                       (ctr["raw_dist"].max() - ctr["raw_dist"].min() + 1e-9)
    ctr["district_clean"] = ctr["district_name"].str.strip().str.upper()
    result = ctr[["district_name","state_name","district_clean","svi_score"]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT, index=False)
    print(f"Proxy SVI built for {len(result):,} districts")
    print("NOTE: This is a simplified proxy SVI (distance-to-urban-centre). For production,")
    print("      replace with Census/NFHS-based indicators.")
    print(f"Output: {len(result):,} rows -> {OUT}")
    print("PASS: svi_scores_v2.csv written (proxy mode)")
