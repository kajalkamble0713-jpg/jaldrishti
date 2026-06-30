"""Final pipeline verification — checks all outputs exist and are valid."""
import pandas as pd, json, joblib
from pathlib import Path

BASE = Path(__file__).parent.parent
PASS, FAIL = "PASS", "FAIL"
results = []

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, label, detail))
    print(f"  [{status}] {label}{(' — '+detail) if detail else ''}")

print("=== PIPELINE VERIFICATION ===\n")

# Data files
for fname, min_rows in [
    ("data/processed/epiclim_labels.csv",               500),
    ("data/processed/nhp_typhoid_labels.csv",           100),
    ("data/processed/district_centroids_v2.csv",        100),
    ("data/processed/svi_scores_v2.csv",                100),
    ("data/processed/final_feature_matrix_district.csv",1000),
    ("data/processed/final_feature_matrix_state.csv",    100),
]:
    p = BASE / fname
    if p.exists():
        df = pd.read_csv(p)
        check(fname, len(df) >= min_rows, f"{len(df):,} rows")
    else:
        check(fname, False, "MISSING")

# Models
for mname in ["add_model.pkl","cholera_model.pkl","typhoid_model.pkl"]:
    p = BASE / "models" / mname
    check(f"models/{mname}", p.exists(), f"{p.stat().st_size:,} bytes" if p.exists() else "MISSING")

# Training report
rpt_path = BASE / "models/training_report.json"
if rpt_path.exists():
    rpt = json.load(open(rpt_path))
    for disease in ["add","cholera","typhoid"]:
        r = rpt.get(disease, {})
        roc = r.get("roc_auc")
        check(f"training_report/{disease}", r.get("status")=="TRAINED",
              f"ROC-AUC={roc:.4f}" if roc else "no AUC")
else:
    check("training_report.json", False, "MISSING")

# SHAP files
for disease in ["add","cholera","typhoid"]:
    p_img = BASE / f"models/shap_summary_{disease}.png"
    p_pkl = BASE / f"models/shap_values_{disease}.pkl"
    check(f"shap_summary_{disease}.png", p_img.exists())
    check(f"shap_values_{disease}.pkl",  p_pkl.exists())

# Dashboard
dash = BASE / "dashboard/app.py"
check("dashboard/app.py", dash.exists() and dash.stat().st_size > 5000,
      f"{dash.stat().st_size:,} bytes" if dash.exists() else "MISSING")

# Mock data
for fname in ["data/processed/mock_feature_matrix_district.csv",
              "data/processed/mock_feature_matrix_state.csv"]:
    p = BASE / fname
    check(fname, p.exists())

print("\n=== SUMMARY ===")
passed = sum(1 for s,_,_ in results if s==PASS)
failed = sum(1 for s,_,_ in results if s==FAIL)
print(f"PASSED: {passed}/{len(results)}")
if failed:
    print(f"FAILED: {failed}")
    for s,l,d in results:
        if s == FAIL:
            print(f"  XX {l} — {d}")
else:
    print("ALL CHECKS PASSED")
print(f"\nFinal status: {'PASS' if failed==0 else 'PARTIAL — see failures above'}")
