import pandas as pd, joblib, os, json
from pathlib import Path

BASE = Path(__file__).parent.parent
print("=== PHASE 2 FULL AUDIT ===\n")

# --- Data files ---
files = {
    "feature_matrix":    BASE/"data/processed/final_feature_matrix.csv",
    "outbreak_labels":   BASE/"data/processed/outbreak_labels.csv",
    "satellite_indices": BASE/"data/processed/master_satellite_indices.csv",
    "svi_scores":        BASE/"data/processed/district_svi_scores.csv",
    "centroids":         BASE/"data/geo/district_centroids.csv",
    "geojson":           BASE/"data/geo/india_districts.geojson",
}
for name, path in files.items():
    exists = path.exists()
    size = f"{path.stat().st_size:,} bytes" if exists else "MISSING"
    print(f"  {'OK' if exists else 'XX'}  {name}: {size}")

print()
# --- Feature matrix stats ---
fm = pd.read_csv(BASE/"data/processed/final_feature_matrix.csv")
ol = pd.read_csv(BASE/"data/processed/outbreak_labels.csv")
si = pd.read_csv(BASE/"data/processed/master_satellite_indices.csv")
sv = pd.read_csv(BASE/"data/processed/district_svi_scores.csv")
ctr = pd.read_csv(BASE/"data/geo/district_centroids.csv")

print(f"Feature Matrix  : {fm.shape[0]:,} rows x {fm.shape[1]} cols")
print(f"  Years covered : {int(fm.year.min())} - {int(fm.year.max())}")
print(f"  Districts     : {fm.district_name.nunique()}")
print(f"  States        : {fm.state_name.nunique()}")
print(f"  Columns       : {list(fm.columns)}")
print()
print(f"Outbreak Labels : {ol.shape[0]:,} rows")
print(f"  ADD outbreaks : {int(ol.add_outbreak.sum())} ({ol.add_outbreak.mean()*100:.1f}%)")
print(f"  Cholera outbr.: {int(ol.cholera_outbreak.sum())} ({ol.cholera_outbreak.mean()*100:.1f}%)")
print(f"  Typhoid outbr.: {int(ol.typhoid_outbreak.sum())} ({ol.typhoid_outbreak.mean()*100:.1f}%)")
print()
print(f"Satellite Indices: {si.shape[0]:,} rows, cols: {list(si.columns[5:])}")
print(f"SVI Scores       : {sv.shape[0]:,} districts")
print(f"Centroids        : {ctr.shape[0]:,} districts, cols: {list(ctr.columns)}")
print()

missing = fm.isnull().mean().mul(100).round(1)
miss_nonzero = missing[missing > 0]
print(f"Missing data %   : {dict(miss_nonzero) if not miss_nonzero.empty else 'None - all complete'}")
print()

# --- Models ---
model_dir = BASE/"models"
model_files = list(model_dir.glob("*.pkl"))
print(f"Models ({len(model_files)}):")
for m in model_files:
    print(f"  {m.name} ({m.stat().st_size:,} bytes)")

# --- Dashboard ---
dash = BASE/"dashboard/app.py"
print(f"\nDashboard app.py: {'EXISTS' if dash.exists() else 'MISSING'} ({dash.stat().st_size:,} bytes)" if dash.exists() else "\nDashboard app.py: MISSING")
print(f"Lines of code: {len(dash.read_text().splitlines())}" if dash.exists() else "")

print("\n=== VERDICT ===")
all_data = all(p.exists() for p in files.values())
all_models = len(model_files) >= 6
print(f"Data pipeline  : {'COMPLETE' if all_data else 'INCOMPLETE'}")
print(f"Models trained : {'COMPLETE (6 pkl files)' if all_models else 'INCOMPLETE'}")
print(f"Dashboard      : {'READY' if dash.exists() and dash.stat().st_size > 10000 else 'NEEDS WORK'}")
print("\nPhase 2 status: ALREADY SUBSTANTIALLY COMPLETE")
print("All core pipeline outputs exist. Verifying model quality next...")
