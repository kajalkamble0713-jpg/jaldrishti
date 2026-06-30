"""
JalDrishti Real Data Pipeline Runner
Runs feature engineering and model training with real satellite + outbreak data
"""

import os
import sys
import shutil
from datetime import datetime
import subprocess

print("=" * 70)
print("JalDrishti Real Data Pipeline Runner")
print("=" * 70)

# ============================================================================
# 1. BACKUP MOCK DATA
# ============================================================================

print("\n📦 Step 1: Backing up mock data...")

backup_dir = f"data/backup/mock_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(backup_dir, exist_ok=True)

mock_files = [
    'data/processed/master_satellite_indices.csv',
    'data/processed/district_svi_scores.csv',
    'data/processed/outbreak_labels.csv',
    'data/processed/final_feature_matrix.csv'
]

backed_up = 0
for file in mock_files:
    if os.path.exists(file):
        dest = os.path.join(backup_dir, os.path.basename(file))
        shutil.copy2(file, dest)
        backed_up += 1
        print(f"  ✓ Backed up: {file}")

if backed_up > 0:
    print(f"\n  ✓ Backed up {backed_up} files to: {backup_dir}")
else:
    print(f"  ℹ️ No mock data files found to backup")

# ============================================================================
# 2. VERIFY REAL DATA FILES EXIST
# ============================================================================

print("\n✅ Step 2: Verifying real data files...")

required_files = {
    'master_satellite_indices.csv': 'data/processed/master_satellite_indices.csv',
    'district_svi_scores.csv': 'data/processed/district_svi_scores.csv',
    'outbreak_labels.csv': 'data/processed/outbreak_labels.csv'
}

missing_files = []

for name, path in required_files.items():
    if os.path.exists(path):
        # Check if it's real data (has LST column for satellite indices)
        if name == 'master_satellite_indices.csv':
            import pandas as pd
            df = pd.read_csv(path)
            
            if 'lst_celsius' in df.columns and df['lst_celsius'].notna().sum() > 0:
                print(f"  ✓ {name} (real data with LST)")
            else:
                print(f"  ⚠️ {name} (missing LST - run nasa_lst_pipeline.py)")
        else:
            print(f"  ✓ {name}")
    else:
        print(f"  ❌ {name} - NOT FOUND")
        missing_files.append(name)

if missing_files:
    print(f"\n❌ Missing required files:")
    for file in missing_files:
        print(f"  - {file}")
    
    print(f"\n📋 Required steps:")
    print(f"  1. Run: python src/download_outbreak_data.py")
    print(f"  2. Run: python src/build_district_filter.py")
    print(f"  3. Run: python src/aws_pipeline.py")
    print(f"  4. Run: python src/nasa_lst_pipeline.py")
    
    sys.exit(1)

# ============================================================================
# 3. RUN FEATURE ENGINEERING
# ============================================================================

print("\n" + "=" * 70)
print("Step 3: Running Feature Engineering")
print("=" * 70)

try:
    result = subprocess.run(
        [sys.executable, 'src/feature_engineering.py'],
        check=True,
        capture_output=False
    )
    
    print("\n✅ Feature engineering completed successfully")

except subprocess.CalledProcessError as e:
    print(f"\n❌ Feature engineering failed with exit code {e.returncode}")
    sys.exit(1)

# Verify feature matrix was created
if not os.path.exists('data/processed/final_feature_matrix.csv'):
    print(f"\n❌ Feature matrix not created")
    sys.exit(1)

# ============================================================================
# 4. RUN MODEL TRAINING
# ============================================================================

print("\n" + "=" * 70)
print("Step 4: Running Model Training")
print("=" * 70)

try:
    result = subprocess.run(
        [sys.executable, 'src/model_trainer.py'],
        check=True,
        capture_output=False
    )
    
    print("\n✅ Model training completed successfully")

except subprocess.CalledProcessError as e:
    print(f"\n❌ Model training failed with exit code {e.returncode}")
    sys.exit(1)

# Verify models were created
models_created = 0
for disease in ['add', 'cholera', 'typhoid']:
    model_path = f'models/trained_model_{disease}.pkl'
    if os.path.exists(model_path):
        models_created += 1

if models_created < 3:
    print(f"\n⚠️ Only {models_created}/3 models created")

# ============================================================================
# 5. SUMMARY
# ============================================================================

print("\n" + "=" * 70)
print("REAL DATA PIPELINE COMPLETE")
print("=" * 70)

print(f"\n📊 Summary:")

# Feature matrix stats
import pandas as pd
feature_df = pd.read_csv('data/processed/final_feature_matrix.csv')

print(f"\n  Feature Matrix:")
print(f"    Rows: {len(feature_df):,}")
print(f"    Districts: {feature_df['district_code'].nunique()}")
print(f"    Year range: {feature_df['year'].min()}-{feature_df['year'].max()}")
print(f"    Features: {len([col for col in feature_df.columns if col not in ['district_code', 'district_name', 'state_name', 'year', 'month', 'add_outbreak', 'cholera_outbreak', 'typhoid_outbreak']])}")

print(f"\n  Outbreak Labels:")
print(f"    ADD: {feature_df['add_outbreak'].sum()} ({feature_df['add_outbreak'].mean()*100:.1f}%)")
print(f"    Cholera: {feature_df['cholera_outbreak'].sum()} ({feature_df['cholera_outbreak'].mean()*100:.1f}%)")
print(f"    Typhoid: {feature_df['typhoid_outbreak'].sum()} ({feature_df['typhoid_outbreak'].mean()*100:.1f}%)")

print(f"\n  Models:")
for disease in ['add', 'cholera', 'typhoid']:
    model_path = f'models/trained_model_{disease}.pkl'
    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        print(f"    {disease.upper()}: ✓ ({size_mb:.1f} MB)")
    else:
        print(f"    {disease.upper()}: ❌")

print(f"\n🚀 NEXT STEPS:")
print(f"  1. Run: streamlit run dashboard/app.py")
print(f"  2. Verify model performance in dashboard")
print(f"  3. Test with different districts and time periods")

print("\n" + "=" * 70)
