"""
JalDrishti District Filter Builder
Generates valid_districts.csv from real EpiClim + IDSP data
Only keeps districts with sufficient outbreak records for ML training
"""

import pandas as pd
import os

# Configuration
MIN_RECORDS = 8  # Minimum outbreak records required per district

print("=" * 70)
print("JalDrishti District Filter Builder")
print("=" * 70)

# Check if raw data files exist
epiclim_path = 'data/raw/epiclim_raw.csv'
idsp_path = 'data/raw/idsp_master_raw.csv'

if not os.path.exists(epiclim_path):
    print(f"\n❌ ERROR: {epiclim_path} not found")
    print("\n📥 Please download EpiClim data first:")
    print("   1. Visit: https://epiclim.org/data")
    print("   2. Download district-level outbreak data")
    print("   3. Save as: data/raw/epiclim_raw.csv")
    exit(1)

if not os.path.exists(idsp_path):
    print(f"\n❌ ERROR: {idsp_path} not found")
    print("\n📥 Please download IDSP data first:")
    print("   1. Visit: https://idsp.nic.in/")
    print("   2. Download master outbreak data")
    print("   3. Save as: data/raw/idsp_master_raw.csv")
    exit(1)

print(f"\n✓ Found raw data files")
print(f"  - {epiclim_path}")
print(f"  - {idsp_path}")

# Load data
print(f"\n📊 Loading data...")
epiclim_df = pd.read_csv(epiclim_path)
idsp_df = pd.read_csv(idsp_path)

print(f"  EpiClim records: {len(epiclim_df):,}")
print(f"  IDSP records: {len(idsp_df):,}")

# Standardize district codes to 6-digit zero-padded strings
print(f"\n🔧 Standardizing district codes...")

# Assuming columns: district_code, district_name, state_name
# Adjust column names based on actual data structure
if 'dtcode' in epiclim_df.columns:
    epiclim_df['district_code'] = epiclim_df['dtcode'].astype(str).str.zfill(6)
elif 'district_code' in epiclim_df.columns:
    epiclim_df['district_code'] = epiclim_df['district_code'].astype(str).str.zfill(6)

if 'dtcode' in idsp_df.columns:
    idsp_df['district_code'] = idsp_df['dtcode'].astype(str).str.zfill(6)
elif 'district_code' in idsp_df.columns:
    idsp_df['district_code'] = idsp_df['district_code'].astype(str).str.zfill(6)

# Count outbreak records per district
print(f"\n📈 Counting outbreak records per district...")

epiclim_counts = epiclim_df.groupby('district_code').size().reset_index(name='epiclim_count')
idsp_counts = idsp_df.groupby('district_code').size().reset_index(name='idsp_count')

# Merge counts
district_counts = epiclim_counts.merge(idsp_counts, on='district_code', how='outer').fillna(0)
district_counts['record_count'] = district_counts['epiclim_count'] + district_counts['idsp_count']

# Get district names and states (from either dataset)
district_info = pd.concat([
    epiclim_df[['district_code', 'district_name', 'state_name']].drop_duplicates(),
    idsp_df[['district_code', 'district_name', 'state_name']].drop_duplicates()
]).drop_duplicates(subset=['district_code'])

# Merge with counts
valid_districts = district_counts.merge(district_info, on='district_code', how='left')

# Filter by minimum records
print(f"\n🔍 Filtering districts with >= {MIN_RECORDS} records...")
print(f"  Before filter: {len(valid_districts)} districts")

valid_districts = valid_districts[valid_districts['record_count'] >= MIN_RECORDS]

print(f"  After filter: {len(valid_districts)} districts")

# Sort by record count
valid_districts = valid_districts.sort_values('record_count', ascending=False)

# Select final columns
valid_districts = valid_districts[['district_code', 'district_name', 'state_name', 'record_count']]

# Save
os.makedirs('data/processed', exist_ok=True)
output_path = 'data/processed/valid_districts.csv'
valid_districts.to_csv(output_path, index=False)

print(f"\n✅ Saved {len(valid_districts)} valid districts → {output_path}")

# Print summary statistics
print(f"\n📊 Summary Statistics:")
print(f"  Total districts: {len(valid_districts)}")
print(f"  Total records: {valid_districts['record_count'].sum():,}")
print(f"  Avg records per district: {valid_districts['record_count'].mean():.1f}")
print(f"  Min records: {valid_districts['record_count'].min()}")
print(f"  Max records: {valid_districts['record_count'].max()}")

# Top 10 districts
print(f"\n🏆 Top 10 Districts by Record Count:")
for idx, row in valid_districts.head(10).iterrows():
    print(f"  {row['district_name']}, {row['state_name']}: {int(row['record_count'])} records")

print("\n" + "=" * 70)
print("✅ DISTRICT FILTER BUILD COMPLETE")
print("=" * 70)
print(f"\n🚀 NEXT STEPS:")
print(f"  1. Run: python src/aws_pipeline.py")
print(f"  2. Run: python src/nasa_lst_pipeline.py")
print(f"  3. Run: python src/feature_engineering.py")
print("=" * 70)
