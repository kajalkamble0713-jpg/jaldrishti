"""
Phase 2 Step 1.1 — Process EpiClim labels (ADD + Cholera, district-level)
Usage: python src/process_epiclim.py
Output: data/processed/epiclim_labels.csv
"""
import pandas as pd
import re
from pathlib import Path

BASE = Path(__file__).parent.parent
RAW  = BASE / "data/raw/epiclim_raw.csv"
OUT  = BASE / "data/processed/epiclim_labels.csv"

def normalize_district(name):
    if pd.isna(name):
        return ""
    s = str(name).strip().upper()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

print("=== process_epiclim.py ===")
print(f"Loading {RAW}...")

if not RAW.exists():
    print(f"FAIL: {RAW} not found. Run Phase 1 setup first.")
    raise SystemExit(1)

df = pd.read_csv(RAW)
print(f"Raw rows: {len(df)}, Columns: {df.columns.tolist()}")
print(df.head(3).to_string())
print()

# Identify disease/date/district columns flexibly
col_lower = {c.lower(): c for c in df.columns}

# Find disease column
disease_col = col_lower.get("disease") or col_lower.get("disease_type") or col_lower.get("illness")
district_col = col_lower.get("district") or col_lower.get("district_name")
state_col = col_lower.get("state") or col_lower.get("state_ut") or col_lower.get("state_name")
date_col = col_lower.get("date") or col_lower.get("week_of_outbreak") or col_lower.get("year")

print(f"Detected cols — disease='{disease_col}', district='{district_col}', state='{state_col}', date='{date_col}'")

# Parse date — the actual EpiClim schema has 'year' and 'mon' columns directly
if "year" in col_lower and "mon" in col_lower:
    df["year"]  = pd.to_numeric(df[col_lower["year"]], errors="coerce")
    df["month"] = pd.to_numeric(df[col_lower["mon"]],  errors="coerce")
    df = df.dropna(subset=["year","month"])
    df["year"]  = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
elif "year" in col_lower and "month" in col_lower:
    df["year"]  = pd.to_numeric(df[col_lower["year"]],  errors="coerce")
    df["month"] = pd.to_numeric(df[col_lower["month"]], errors="coerce")
    df = df.dropna(subset=["year","month"])
    df["year"]  = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
elif "week_of_outbreak" in col_lower:
    # fallback: try to extract year from other columns
    df["year"]  = pd.to_numeric(df.get("year", None), errors="coerce") if "year" in df else None
    df["month"] = pd.to_numeric(df.get("mon",  None), errors="coerce") if "mon"  in df else None
    df = df.dropna(subset=["year","month"])
    df["year"]  = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
else:
    print("WARN: Cannot parse date from columns. Attempting generic parse.")
    df["year"]  = pd.to_datetime(df[date_col], errors="coerce").dt.year
    df["month"] = pd.to_datetime(df[date_col], errors="coerce").dt.month
    df = df.dropna(subset=["year","month"])
    df["year"]  = df["year"].astype(int)
    df["month"] = df["month"].astype(int)

print(f"Date range: {df.year.min()}-{df.month.min():02d} to {df.year.max()}-{df.month.max():02d}")

# Filter to ADD and Cholera
add_kw     = ["diarrhoea","diarrhea","diarrhoeal","add","acute diarrhoeal"]
cholera_kw = ["cholera"]
df["disease_lc"] = df[disease_col].astype(str).str.lower().str.strip()
df_add     = df[df["disease_lc"].str.contains("|".join(add_kw),    na=False)].copy()
df_cholera = df[df["disease_lc"].str.contains("|".join(cholera_kw), na=False)].copy()
print(f"ADD rows: {len(df_add)}, Cholera rows: {len(df_cholera)}")

# Normalize district names
for d in [df_add, df_cholera]:
    d["district_clean"] = d[district_col].apply(normalize_district)
    d["state_clean"]    = d[state_col].astype(str).str.strip().str.upper() if state_col else ""

# Aggregate to district-month binary labels
def agg_labels(data, flag_col):
    grp = data.groupby(["district_clean","state_clean","year","month"]).size().reset_index(name="count")
    grp[flag_col] = 1
    return grp[["district_clean","state_clean","year","month",flag_col]]

add_labels     = agg_labels(df_add,     "outbreak_add")
cholera_labels = agg_labels(df_cholera, "outbreak_cholera")

# Build all district-month combinations present in either
all_districts = pd.concat([
    add_labels[["district_clean","state_clean","year","month"]],
    cholera_labels[["district_clean","state_clean","year","month"]]
]).drop_duplicates()

result = all_districts.merge(add_labels,     on=["district_clean","state_clean","year","month"], how="left")\
                      .merge(cholera_labels, on=["district_clean","state_clean","year","month"], how="left")
result["outbreak_add"]     = result["outbreak_add"].fillna(0).astype(int)
result["outbreak_cholera"] = result["outbreak_cholera"].fillna(0).astype(int)
result = result.sort_values(["state_clean","district_clean","year","month"]).reset_index(drop=True)

OUT.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(OUT, index=False)

print(f"\nOutput: {len(result):,} rows -> {OUT}")
print(f"ADD outbreaks   : {result.outbreak_add.sum()} ({result.outbreak_add.mean()*100:.1f}%)")
print(f"Cholera outbreaks: {result.outbreak_cholera.sum()} ({result.outbreak_cholera.mean()*100:.1f}%)")
print(f"Unique districts : {result.district_clean.nunique()}")
print(f"Years covered    : {result.year.min()} - {result.year.max()}")
print("\nPASS: epiclim_labels.csv written")
