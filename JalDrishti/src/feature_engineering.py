"""
JalDrishti Feature Engineering Pipeline
Builds the final ML feature matrix with lag features, rolling means, and SVI fusion
"""

import pandas as pd
import numpy as np
import os

print("=" * 70)
print("JalDrishti Feature Engineering Pipeline")
print("=" * 70)

# Load data
print("\n📊 Loading data files...")

try:
    satellite_df = pd.read_csv('data/processed/master_satellite_indices.csv')
    print(f"  ✓ Loaded satellite indices: {len(satellite_df):,} rows")
except FileNotFoundError:
    print("  ❌ master_satellite_indices.csv not found")
    print("  Run: python src/generate_mock_data.py")
    exit(1)

try:
    svi_df = pd.read_csv('data/processed/district_svi_scores.csv')
    print(f"  ✓ Loaded SVI scores: {len(svi_df):,} rows")
except FileNotFoundError:
    print("  ❌ district_svi_scores.csv not found")
    print("  Run: python src/generate_mock_data.py")
    exit(1)

try:
    labels_df = pd.read_csv('data/processed/outbreak_labels.csv')
    print(f"  ✓ Loaded outbreak labels: {len(labels_df):,} rows")
except FileNotFoundError:
    print("  ❌ outbreak_labels.csv not found")
    print("  Run: python src/generate_mock_data.py")
    exit(1)

# Standardize district codes
print("\n🔧 Standardizing district codes...")
satellite_df['district_code'] = satellite_df['district_code'].astype(str).str.zfill(6)
svi_df['district_code'] = svi_df['district_code'].astype(str).str.zfill(6)
labels_df['district_code'] = labels_df['district_code'].astype(str).str.zfill(6)

# Merge satellite and labels
print("\n🔗 Merging satellite indices with outbreak labels...")
df = satellite_df.merge(
    labels_df,
    on=['district_code', 'district_name', 'state_name', 'year', 'month'],
    how='left'
)
print(f"  Merged shape: {df.shape}")

# Sort by district and time
df = df.sort_values(['district_code', 'year', 'month']).reset_index(drop=True)

# Define satellite indices
SATELLITE_INDICES = ['turbidity', 'ndci', 'cdom', 'ndwi', 'awei', 'lst_celsius']

print("\n⏱ Creating lag features...")
# Create 1-month and 2-month lag features
for idx in SATELLITE_INDICES:
    df[f'{idx}_lag1'] = df.groupby('district_code')[idx].shift(1)
    df[f'{idx}_lag2'] = df.groupby('district_code')[idx].shift(2)

print(f"  ✓ Created {len(SATELLITE_INDICES) * 2} lag features")

print("\n📊 Creating rolling mean features...")
# Create 3-month rolling mean features
for idx in SATELLITE_INDICES:
    df[f'{idx}_roll3'] = df.groupby('district_code')[idx].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )

print(f"  ✓ Created {len(SATELLITE_INDICES)} rolling mean features")

print("\n🌧 Creating monsoon flag...")
# Create monsoon flag (June-September)
df['is_monsoon'] = df['month'].apply(lambda x: 1 if x in [6, 7, 8, 9] else 0)
print(f"  ✓ Monsoon months flagged: {df['is_monsoon'].sum():,} rows")

print("\n📈 Creating year-over-year delta features...")
# Create year-over-year delta (current month vs same month last year)
for idx in SATELLITE_INDICES:
    df[f'{idx}_yoy_delta'] = df.groupby(['district_code', 'month'])[idx].diff()

print(f"  ✓ Created {len(SATELLITE_INDICES)} YoY delta features")

print("\n🏘 Merging SVI scores...")
# Merge SVI scores
df = df.merge(svi_df[['district_code', 'svi_score']], on='district_code', how='left')
print(f"  ✓ SVI scores merged")

# Fill missing SVI with median
if df['svi_score'].isna().any():
    median_svi = df['svi_score'].median()
    df['svi_score'].fillna(median_svi, inplace=True)
    print(f"  ⚠ Filled {df['svi_score'].isna().sum()} missing SVI values with median: {median_svi:.3f}")

print("\n🧹 Dropping rows with NaN in features...")
# Drop rows with any NaN in features (lag creation creates NaN at start of each district's series)
initial_rows = len(df)
df = df.dropna(subset=[col for col in df.columns if col not in ['district_code', 'district_name', 'state_name']])
dropped_rows = initial_rows - len(df)
print(f"  Dropped {dropped_rows:,} rows with NaN")
print(f"  Remaining rows: {len(df):,}")

# Save final feature matrix
output_path = 'data/processed/final_feature_matrix.csv'
df.to_csv(output_path, index=False)

print(f"\n✅ Saved final feature matrix → {output_path}")
print(f"\n📊 Final Feature Matrix Summary:")
print(f"  Shape: {df.shape}")
print(f"  Districts: {df['district_code'].nunique()}")
print(f"  Time range: {df['year'].min()}-{df['year'].max()}")
print(f"  Total features: {len(df.columns)}")

print(f"\n📋 Feature Columns:")
feature_cols = [col for col in df.columns if col not in ['district_code', 'district_name', 'state_name', 'year', 'month', 'add_outbreak', 'cholera_outbreak', 'typhoid_outbreak']]
for i, col in enumerate(feature_cols, 1):
    print(f"  {i:2d}. {col}")

print(f"\n🎯 Target Columns:")
print(f"  - add_outbreak: {df['add_outbreak'].sum()} positive cases ({df['add_outbreak'].mean()*100:.1f}%)")
print(f"  - cholera_outbreak: {df['cholera_outbreak'].sum()} positive cases ({df['cholera_outbreak'].mean()*100:.1f}%)")
print(f"  - typhoid_outbreak: {df['typhoid_outbreak'].sum()} positive cases ({df['typhoid_outbreak'].mean()*100:.1f}%)")

print("\n" + "=" * 70)
print("✅ FEATURE ENGINEERING COMPLETE")
print("=" * 70)
print(f"\n🚀 NEXT STEPS:")
print(f"  1. Run: python src/model_trainer.py")
print(f"  2. Run: streamlit run dashboard/app.py")
print("=" * 70)
