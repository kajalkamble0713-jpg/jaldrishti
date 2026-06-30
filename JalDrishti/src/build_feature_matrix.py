"""
Phase 2 Step 5 — Build Final Feature Matrix
Usage: python src/build_feature_matrix.py
Output: data/processed/final_feature_matrix_district.csv
        data/processed/final_feature_matrix_state.csv
"""
import pandas as pd, numpy as np
from pathlib import Path

BASE = Path(__file__).parent.parent

# Input paths
SAT_IDX  = BASE / "data/processed/master_satellite_indices.csv"
LABELS   = BASE / "data/processed/outbreak_labels.csv"
SVI      = BASE / "data/processed/district_svi_scores.csv"
OUT_D    = BASE / "data/processed/final_feature_matrix_district.csv"
OUT_S    = BASE / "data/processed/final_feature_matrix_state.csv"

print("=== build_feature_matrix.py ===")

# Load base data
print("Loading satellite indices...")
sat = pd.read_csv(SAT_IDX)
print(f"  {len(sat):,} rows, cols: {list(sat.columns)}")

print("Loading outbreak labels...")
labels = pd.read_csv(LABELS)
print(f"  {len(labels):,} rows")

print("Loading SVI scores...")
svi = pd.read_csv(SVI)[["district_name","svi_score"]]
print(f"  {len(svi):,} districts")

# Merge satellite + labels on district_code, year, month
df = sat.merge(labels[["district_code","district_name","state_name","year","month",
                        "add_outbreak","cholera_outbreak","typhoid_outbreak"]],
               on=["district_code","district_name","state_name","year","month"],
               how="inner")
print(f"\nAfter satellite + labels merge: {len(df):,} rows")

# Merge SVI
df = df.merge(svi, on="district_name", how="left")
df["svi_score"] = df["svi_score"].fillna(df["svi_score"].median())
print(f"After SVI merge: {len(df):,} rows, missing SVI: {df.svi_score.isna().sum()}")

# Sort for lag computation
df = df.sort_values(["district_code","year","month"]).reset_index(drop=True)

# Lag features (1-month, 2-month)
idx_cols = ["turbidity","ndci","cdom","ndwi","awei","lst_celsius"]
for col in idx_cols:
    df[f"{col}_lag1"] = df.groupby("district_code")[col].shift(1)
    df[f"{col}_lag2"] = df.groupby("district_code")[col].shift(2)

# 3-month rolling mean
for col in idx_cols:
    df[f"{col}_roll3"] = (df.groupby("district_code")[col]
                            .transform(lambda x: x.rolling(3, min_periods=1).mean()))

# Monsoon flag
df["is_monsoon"] = df["month"].isin([6,7,8,9]).astype(int)

# YoY delta (vs same month prior year)
df["year_month_key"] = df["year"].astype(str) + "_" + df["month"].astype(str).str.zfill(2)
prev_year = df.copy()
prev_year["year"] += 1
prev_year = prev_year.rename(columns={c: f"{c}_prev" for c in idx_cols})
df = df.merge(prev_year[["district_code","year","month"] + [f"{c}_prev" for c in idx_cols]],
              on=["district_code","year","month"], how="left")
for col in idx_cols:
    df[f"{col}_yoy_delta"] = df[col] - df[f"{col}_prev"]
    df = df.drop(columns=[f"{col}_prev"])

df = df.drop(columns=["year_month_key"], errors="ignore")

# Drop rows where lags are all NaN (first 2 months per district)
lag_cols = [f"{c}_lag1" for c in idx_cols]
df = df.dropna(subset=lag_cols).reset_index(drop=True)

print(f"\nAfter lag/feature engineering: {len(df):,} rows")

# Missing data report
miss = df.isnull().mean().mul(100).round(1)
miss_nonzero = miss[miss > 0]
print(f"Missing %: {dict(miss_nonzero) if not miss_nonzero.empty else 'None'}")

# Class balance
print(f"\nClass balance:")
print(f"  ADD outbreak    : {df.add_outbreak.sum():,} / {len(df):,} ({df.add_outbreak.mean()*100:.1f}%)")
print(f"  Cholera outbreak: {df.cholera_outbreak.sum():,} / {len(df):,} ({df.cholera_outbreak.mean()*100:.1f}%)")
print(f"  Typhoid outbreak: {df.typhoid_outbreak.sum():,} / {len(df):,} ({df.typhoid_outbreak.mean()*100:.1f}%)")

# Save district-level (ADD + Cholera)
OUT_D.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_D, index=False)
print(f"\nDistrict matrix: {len(df):,} rows -> {OUT_D}")

# Build state-level table for Typhoid
state_agg = df.groupby(["state_name","year","month"]).agg(
    {**{c: "mean" for c in idx_cols},
     **{f"{c}_lag1": "mean" for c in idx_cols},
     **{f"{c}_roll3": "mean" for c in idx_cols},
     "svi_score": "mean",
     "is_monsoon": "max",
     "typhoid_outbreak": "max"}
).reset_index()
state_agg.to_csv(OUT_S, index=False)
print(f"State matrix   : {len(state_agg):,} rows -> {OUT_S}")

print("\nPASS: Feature matrices written")
