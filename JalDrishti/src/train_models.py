"""
Phase 2 Step 6 — Train Models
Usage: python src/train_models.py
Output: models/add_model.pkl, models/cholera_model.pkl, models/typhoid_model.pkl
        models/training_report.json
"""
import pandas as pd, numpy as np, json, joblib
from pathlib import Path
from sklearn.metrics import roc_auc_score, average_precision_score, classification_report
from xgboost import XGBClassifier

BASE    = Path(__file__).parent.parent
FM_D    = BASE / "data/processed/final_feature_matrix_district.csv"
FM_S    = BASE / "data/processed/final_feature_matrix_state.csv"
MDL_DIR = BASE / "models"
MDL_DIR.mkdir(exist_ok=True)

# Feature columns (no target, no meta)
META_COLS   = ["district_code","district_name","state_name","year","month"]
TARGET_COLS = ["add_outbreak","cholera_outbreak","typhoid_outbreak"]

def get_feature_cols(df):
    return [c for c in df.columns if c not in META_COLS + TARGET_COLS]

def temporal_split(df, train_pct=0.6, val_pct=0.2):
    """Strict temporal split — sort by year/month, no shuffling."""
    df = df.sort_values(["year","month"]).reset_index(drop=True)
    n = len(df)
    t = int(n * train_pct)
    v = int(n * (train_pct + val_pct))
    return df.iloc[:t], df.iloc[t:v], df.iloc[v:]

def train_disease(name, df, target_col):
    print(f"\n--- Training {name.upper()} ---")
    feat_cols = get_feature_cols(df)
    df_clean = df.dropna(subset=feat_cols + [target_col]).copy()
    print(f"  Rows: {len(df_clean):,}, Features: {len(feat_cols)}")

    if len(df_clean) < 50:
        print(f"  WARN: Too few rows ({len(df_clean)}) — skipping model, reporting limitation")
        return None, {"status": "SKIPPED", "reason": f"Only {len(df_clean)} rows"}

    train, val, test = temporal_split(df_clean)
    print(f"  Train: {len(train):,} | Val: {len(val):,} | Test: {len(test):,}")
    print(f"  Train years: {int(train.year.min())}-{int(train.year.max())}  "
          f"Test years: {int(test.year.min())}-{int(test.year.max())}")

    y_train = train[target_col]
    pos_count = int(y_train.sum())
    neg_count = int((y_train == 0).sum())
    if pos_count == 0:
        print(f"  WARN: No positive samples in training set — skipping")
        return None, {"status": "SKIPPED", "reason": "No positive training samples"}
    scale_pw = neg_count / pos_count
    print(f"  Class balance (train): {pos_count} pos / {neg_count} neg  scale_pos_weight={scale_pw:.1f}")

    model = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pw,
        eval_metric="logloss",
        use_label_encoder=False,
        random_state=42,
        verbosity=0,
    )
    model.fit(train[feat_cols], y_train,
              eval_set=[(val[feat_cols], val[target_col])],
              verbose=False)

    # Evaluate on test
    if len(test) == 0 or test[target_col].sum() == 0:
        print(f"  WARN: Test set has no positives — ROC-AUC not meaningful")
        roc, pr = None, None
    else:
        y_prob = model.predict_proba(test[feat_cols])[:,1]
        roc = float(roc_auc_score(test[target_col], y_prob))
        pr  = float(average_precision_score(test[target_col], y_prob))
        print(f"  ROC-AUC: {roc:.4f}  PR-AUC: {pr:.4f}")

    # Save model
    model_path = MDL_DIR / f"{name}_model.pkl"
    joblib.dump(model, model_path)
    print(f"  Saved: {model_path}")

    report = {
        "status": "TRAINED",
        "disease": name,
        "target": target_col,
        "train_rows": len(train),
        "val_rows": len(val),
        "test_rows": len(test),
        "train_years": f"{int(train.year.min())}-{int(train.year.max())}",
        "test_years": f"{int(test.year.min())}-{int(test.year.max())}",
        "roc_auc": roc,
        "pr_auc": pr,
        "features": feat_cols,
        "model_path": str(model_path),
    }
    return model, report

print("=== train_models.py ===")

df_d = pd.read_csv(FM_D)
df_s = pd.read_csv(FM_S)
print(f"District matrix: {len(df_d):,} rows")
print(f"State matrix   : {len(df_s):,} rows")

reports = {}

# Train ADD (district)
add_model, add_report = train_disease("add", df_d, "add_outbreak")
reports["add"] = add_report

# Train Cholera (district)
cho_model, cho_report = train_disease("cholera", df_d, "cholera_outbreak")
reports["cholera"] = cho_report

# Train Typhoid (state-level)
# Rename state_name to match get_feature_cols expectation
df_s_t = df_s.rename(columns={"state_name": "district_name"}) if "state_name" in df_s.columns else df_s
df_s_t["district_code"] = 0  # placeholder so META_COLS filter works
typ_model, typ_report = train_disease("typhoid", df_s_t, "typhoid_outbreak")
reports["typhoid"] = typ_report

# Save training report
report_path = MDL_DIR / "training_report.json"
with open(report_path, "w") as f:
    json.dump(reports, f, indent=2, default=str)
print(f"\nTraining report saved: {report_path}")

# Summary
print("\n=== RESULTS SUMMARY ===")
for disease, rep in reports.items():
    st = rep.get("status","?")
    roc = rep.get("roc_auc")
    pr  = rep.get("pr_auc")
    roc_str = f"ROC-AUC={roc:.4f}" if roc else "ROC-AUC=N/A"
    pr_str  = f"PR-AUC={pr:.4f}"  if pr  else "PR-AUC=N/A"
    print(f"  {disease.upper():10s}: {st:10s}  {roc_str}  {pr_str}")

print("\nPASS: train_models.py complete")
