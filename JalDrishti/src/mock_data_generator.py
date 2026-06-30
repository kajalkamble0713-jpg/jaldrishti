"""
Phase 2 Step 9 — Mock Data Generator (safety net for dashboard demos)
Usage: python src/mock_data_generator.py
Output: data/processed/mock_feature_matrix_district.csv
        data/processed/mock_feature_matrix_state.csv
        models/mock_add_model.pkl (tiny dummy model)
NOTE: Dashboard uses these ONLY when real data is unavailable.
      A visible "DEMO DATA" banner is shown when mock data is active.
"""
import pandas as pd, numpy as np, joblib
from pathlib import Path
from xgboost import XGBClassifier
from sklearn.datasets import make_classification

BASE    = Path(__file__).parent.parent
OUT_D   = BASE / "data/processed/mock_feature_matrix_district.csv"
OUT_S   = BASE / "data/processed/mock_feature_matrix_state.csv"
MDL_DIR = BASE / "models"
MDL_DIR.mkdir(exist_ok=True)

np.random.seed(42)

DISTRICTS = [
    ("Patna","Bihar"),("Varanasi","Uttar Pradesh"),("Kolkata","West Bengal"),
    ("Mumbai","Maharashtra"),("Chennai","Tamil Nadu"),("Hyderabad","Telangana"),
    ("Bhopal","Madhya Pradesh"),("Jaipur","Rajasthan"),("Lucknow","Uttar Pradesh"),
    ("Agra","Uttar Pradesh"),
]
STATES = list({s for _,s in DISTRICTS})
YEARS  = [2022, 2023]
MONTHS = range(1, 13)

IDX_COLS = ["turbidity","ndci","cdom","ndwi","awei","lst_celsius"]

rows = []
for dist, state in DISTRICTS:
    for year in YEARS:
        for month in MONTHS:
            is_monsoon = int(month in [6,7,8,9])
            base_turb  = 0.12 + is_monsoon*0.05 + np.random.normal(0,0.03)
            lst        = 25 + is_monsoon*3 + np.random.normal(0,2)
            row = {
                "district_code": hash(dist) % 100000,
                "district_name": dist, "state_name": state,
                "year": year, "month": month,
                "turbidity":   max(0, base_turb),
                "ndci":        np.random.uniform(0.02, 0.15),
                "cdom":        np.random.uniform(0.3, 0.9),
                "ndwi":        np.random.uniform(-0.2, 0.2),
                "awei":        np.random.uniform(-0.3, 0.1),
                "lst_celsius": max(15, min(45, lst)),
                "svi_score":   np.random.uniform(0.3, 0.8),
                "is_monsoon":  is_monsoon,
            }
            # Simple synthetic outbreak logic
            risk = row["turbidity"]*2 + is_monsoon*0.3 + row["svi_score"]*0.2
            row["add_outbreak"]     = int(risk + np.random.normal(0,0.3) > 0.65)
            row["cholera_outbreak"] = int(risk + np.random.normal(0,0.4) > 0.80)
            row["typhoid_outbreak"] = int(risk + np.random.normal(0,0.3) > 0.72)
            rows.append(row)

df = pd.DataFrame(rows)

# Add lag columns
for col in IDX_COLS:
    df[f"{col}_lag1"] = df.groupby("district_name")[col].shift(1).fillna(df[col])
    df[f"{col}_lag2"] = df.groupby("district_name")[col].shift(2).fillna(df[col])
    df[f"{col}_roll3"] = df.groupby("district_name")[col].transform(
        lambda x: x.rolling(3, min_periods=1).mean())
    df[f"{col}_yoy_delta"] = np.random.normal(0, 0.01, len(df))

df.to_csv(OUT_D, index=False)
print(f"Mock district matrix: {len(df):,} rows -> {OUT_D}")

# State-level mock
state_rows = []
for state in STATES:
    for year in YEARS:
        for month in MONTHS:
            is_monsoon = int(month in [6,7,8,9])
            row = {"state_name": state, "year": year, "month": month,
                   "turbidity": np.random.uniform(0.1,0.2),
                   "ndci": np.random.uniform(0.03,0.12),
                   "cdom": np.random.uniform(0.4,0.8),
                   "ndwi": np.random.uniform(-0.15,0.1),
                   "awei": np.random.uniform(-0.25,0.05),
                   "lst_celsius": 25+is_monsoon*3+np.random.normal(0,2),
                   "svi_score": np.random.uniform(0.4,0.7),
                   "is_monsoon": is_monsoon,
                   "typhoid_outbreak": int(np.random.random() < 0.15)}
            for col in IDX_COLS:
                row[f"{col}_lag1"]  = row[col] + np.random.normal(0,0.01)
                row[f"{col}_roll3"] = row[col] + np.random.normal(0,0.005)
            state_rows.append(row)

df_s = pd.DataFrame(state_rows)
df_s.to_csv(OUT_S, index=False)
print(f"Mock state matrix  : {len(df_s):,} rows -> {OUT_S}")

# Tiny dummy models for dashboard rendering
feat_cols = [c for c in df.columns if c not in
             ["district_code","district_name","state_name","year","month",
              "add_outbreak","cholera_outbreak","typhoid_outbreak"]]
X = df[feat_cols].fillna(0).values
for disease, target in [("add","add_outbreak"),("cholera","cholera_outbreak"),("typhoid","typhoid_outbreak")]:
    y = df[target].values
    m = XGBClassifier(n_estimators=10, max_depth=2, verbosity=0, use_label_encoder=False)
    m.fit(X, y)
    out = MDL_DIR / f"mock_{disease}_model.pkl"
    joblib.dump(m, out)
    print(f"Mock model: {out}")

print("PASS: mock_data_generator.py complete")
