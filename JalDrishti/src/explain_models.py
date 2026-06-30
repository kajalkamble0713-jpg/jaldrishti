"""
Phase 2 Step 7 — SHAP Explainability
Usage: python src/explain_models.py
Output: models/shap_summary_add.png, models/shap_summary_cholera.png,
        models/shap_summary_typhoid.png, models/shap_values_*.pkl
"""
import pandas as pd, numpy as np, joblib, json, shap, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

BASE    = Path(__file__).parent.parent
FM_D    = BASE / "data/processed/final_feature_matrix_district.csv"
FM_S    = BASE / "data/processed/final_feature_matrix_state.csv"
MDL_DIR = BASE / "models"
RPT     = MDL_DIR / "training_report.json"

META_COLS   = ["district_code","district_name","state_name","year","month"]
TARGET_COLS = ["add_outbreak","cholera_outbreak","typhoid_outbreak"]

def get_feature_cols(df):
    return [c for c in df.columns if c not in META_COLS + TARGET_COLS]

def temporal_test_split(df, test_pct=0.2):
    df = df.sort_values(["year","month"]).reset_index(drop=True)
    n  = len(df)
    t  = int(n * (1 - test_pct))
    return df.iloc[t:]

print("=== explain_models.py ===")

with open(RPT) as f:
    report = json.load(f)

df_d = pd.read_csv(FM_D)
df_s = pd.read_csv(FM_S)

tasks = [
    ("add",     df_d,  "add_outbreak"),
    ("cholera", df_d,  "cholera_outbreak"),
    ("typhoid", df_s,  "typhoid_outbreak"),
]

for name, df_raw, target in tasks:
    print(f"\n--- SHAP for {name.upper()} ---")
    model_path = MDL_DIR / f"{name}_model.pkl"
    if not model_path.exists():
        print(f"  SKIP: {model_path} not found")
        continue

    model = joblib.load(model_path)

    # Prepare data same way as training
    if name == "typhoid":
        df = df_raw.rename(columns={"state_name": "district_name"}).copy()
        df["district_code"] = 0
    else:
        df = df_raw.copy()

    feat_cols = get_feature_cols(df)
    df_clean  = df.dropna(subset=feat_cols + [target])
    test_df   = temporal_test_split(df_clean)

    if len(test_df) < 5:
        print(f"  SKIP: Test set too small ({len(test_df)} rows)")
        continue

    X_test = test_df[feat_cols]
    print(f"  Computing SHAP on {len(X_test)} test rows...")

    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)

    # Save raw SHAP values
    shap_path = MDL_DIR / f"shap_values_{name}.pkl"
    joblib.dump({"shap_values": shap_values, "feature_names": feat_cols,
                 "X_test": X_test.values}, shap_path)
    print(f"  Saved SHAP values: {shap_path}")

    # Top-10 bar chart
    mean_abs = np.abs(shap_values).mean(axis=0)
    top10_idx = np.argsort(mean_abs)[-10:][::-1]
    top10_names = [feat_cols[i] for i in top10_idx]
    top10_vals  = mean_abs[top10_idx]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top10_names[::-1], top10_vals[::-1], color="#0D9488")
    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title(f"Top-10 Feature Importances — {name.upper()}")
    ax.tick_params(labelsize=9)
    plt.tight_layout()
    img_path = MDL_DIR / f"shap_summary_{name}.png"
    plt.savefig(img_path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  Saved chart: {img_path}")
    print(f"  Top-3 features: {top10_names[:3]}")

print("\nPASS: explain_models.py complete")
