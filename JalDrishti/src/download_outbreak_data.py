"""
JalDrishti Real Outbreak Data Downloader
Downloads and integrates EpiClim + IDSP outbreak data for model training
"""

import os
import pandas as pd
import requests
from pathlib import Path
import json

print("=" * 70)
print("JalDrishti Real Outbreak Data Downloader")
print("=" * 70)

# Create directories
os.makedirs('data/raw', exist_ok=True)
os.makedirs('data/processed', exist_ok=True)

# ============================================================================
# 1. DOWNLOAD EPICLIM DATA
# ============================================================================

print("\n📥 Step 1: Downloading EpiClim outbreak data...")

EPICLIM_URL = "https://zenodo.org/records/14580510/files/epiclim_outbreaks.csv?download=1"
EPICLIM_PATH = "data/raw/epiclim_raw.csv"

try:
    print(f"  URL: {EPICLIM_URL}")
    response = requests.get(EPICLIM_URL, timeout=60)
    response.raise_for_status()
    
    with open(EPICLIM_PATH, 'wb') as f:
        f.write(response.content)
    
    print(f"  ✓ Downloaded to {EPICLIM_PATH}")
    print(f"  File size: {os.path.getsize(EPICLIM_PATH) / 1024:.1f} KB")

except requests.exceptions.RequestException as e:
    print(f"  ❌ Download failed: {e}")
    print(f"\n  MANUAL DOWNLOAD REQUIRED:")
    print(f"  1. Visit: https://zenodo.org/records/14580510")
    print(f"  2. Download 'epiclim_outbreaks.csv'")
    print(f"  3. Save to: {EPICLIM_PATH}")
    print(f"  4. Re-run this script")
    
    if not os.path.exists(EPICLIM_PATH):
        print(f"\n  ⚠️ Cannot proceed without EpiClim data. Exiting.")
        exit(1)
    else:
        print(f"  ✓ Found existing file at {EPICLIM_PATH}")

# ============================================================================
# 2. DOWNLOAD IDSP DATA
# ============================================================================

print("\n📥 Step 2: Downloading IDSP Master Dataset...")

IDSP_PATH = "data/raw/idsp_master_raw.csv"

# IDSP data requires manual download from dataful.in
print(f"  ⚠️ IDSP data requires manual download")
print(f"\n  MANUAL DOWNLOAD INSTRUCTIONS:")
print(f"  1. Visit: https://dataful.in/datasets/18514/")
print(f"  2. Click 'Download' button")
print(f"  3. Save CSV file as: {IDSP_PATH}")
print(f"  4. Re-run this script")

if not os.path.exists(IDSP_PATH):
    print(f"\n  ❌ IDSP data not found at {IDSP_PATH}")
    print(f"  Proceeding with EpiClim data only...")
    use_idsp = False
else:
    print(f"  ✓ Found IDSP data at {IDSP_PATH}")
    use_idsp = True

# ============================================================================
# 3. LOAD AND STANDARDIZE DATA
# ============================================================================

print("\n🔧 Step 3: Loading and standardizing outbreak data...")

# Load EpiClim
try:
    epiclim_df = pd.read_csv(EPICLIM_PATH)
    print(f"  ✓ Loaded EpiClim: {len(epiclim_df):,} rows")
    print(f"    Columns: {list(epiclim_df.columns)}")
except Exception as e:
    print(f"  ❌ Failed to load EpiClim: {e}")
    exit(1)

# Load IDSP (if available)
if use_idsp:
    try:
        idsp_df = pd.read_csv(IDSP_PATH)
        print(f"  ✓ Loaded IDSP: {len(idsp_df):,} rows")
        print(f"    Columns: {list(idsp_df.columns)}")
    except Exception as e:
        print(f"  ⚠️ Failed to load IDSP: {e}")
        print(f"  Proceeding with EpiClim only...")
        use_idsp = False

# ============================================================================
# 4. STANDARDIZE DISTRICT CODES
# ============================================================================

print("\n🔧 Step 4: Standardizing district codes...")

# Detect district code column (common variations)
district_code_cols = ['district_code', 'dtcode', 'dist_code', 'lgd_code', 'census_code']

def find_district_code_col(df):
    """Find the district code column in dataframe"""
    for col in district_code_cols:
        if col in df.columns:
            return col
    # Try case-insensitive match
    for col in df.columns:
        if 'district' in col.lower() and 'code' in col.lower():
            return col
    return None

# Standardize EpiClim
epiclim_code_col = find_district_code_col(epiclim_df)
if epiclim_code_col:
    epiclim_df['district_code'] = epiclim_df[epiclim_code_col].astype(str).str.zfill(6)
    print(f"  ✓ EpiClim: Standardized '{epiclim_code_col}' to 6-digit format")
else:
    print(f"  ⚠️ EpiClim: No district code column found. Available columns:")
    print(f"    {list(epiclim_df.columns)}")
    print(f"  Please manually specify the district code column name.")
    exit(1)

# Standardize IDSP
if use_idsp:
    idsp_code_col = find_district_code_col(idsp_df)
    if idsp_code_col:
        idsp_df['district_code'] = idsp_df[idsp_code_col].astype(str).str.zfill(6)
        print(f"  ✓ IDSP: Standardized '{idsp_code_col}' to 6-digit format")
    else:
        print(f"  ⚠️ IDSP: No district code column found")
        use_idsp = False

# ============================================================================
# 5. EXTRACT DISEASE OUTBREAK LABELS
# ============================================================================

print("\n🦠 Step 5: Extracting disease outbreak labels...")

# Expected columns: district_code, district_name, state_name, year, month, disease_type

def extract_outbreak_labels(df, source_name):
    """Extract outbreak labels from raw data"""
    
    # Detect disease column
    disease_cols = ['disease', 'disease_type', 'disease_name', 'pathogen']
    disease_col = None
    for col in disease_cols:
        if col in df.columns:
            disease_col = col
            break
    
    if not disease_col:
        print(f"  ⚠️ {source_name}: No disease column found")
        return None
    
    # Detect date columns
    year_col = 'year' if 'year' in df.columns else None
    month_col = 'month' if 'month' in df.columns else None
    
    if not year_col or not month_col:
        # Try to extract from date column
        date_cols = ['date', 'outbreak_date', 'report_date']
        for col in date_cols:
            if col in df.columns:
                df['date_parsed'] = pd.to_datetime(df[col], errors='coerce')
                df['year'] = df['date_parsed'].dt.year
                df['month'] = df['date_parsed'].dt.month
                year_col = 'year'
                month_col = 'month'
                break
    
    if not year_col or not month_col:
        print(f"  ⚠️ {source_name}: No date columns found")
        return None
    
    # Map disease names to standard labels
    disease_mapping = {
        'add': 'add_outbreak',
        'acute diarrhoeal disease': 'add_outbreak',
        'diarrhoea': 'add_outbreak',
        'diarrhea': 'add_outbreak',
        'cholera': 'cholera_outbreak',
        'typhoid': 'typhoid_outbreak',
        'enteric fever': 'typhoid_outbreak',
    }
    
    # Create outbreak labels
    df['disease_lower'] = df[disease_col].astype(str).str.lower().str.strip()
    
    # Initialize outbreak columns
    df['add_outbreak'] = 0
    df['cholera_outbreak'] = 0
    df['typhoid_outbreak'] = 0
    
    # Map diseases
    for disease_key, outbreak_col in disease_mapping.items():
        mask = df['disease_lower'].str.contains(disease_key, na=False)
        df.loc[mask, outbreak_col] = 1
    
    # Group by district, year, month (aggregate multiple outbreaks)
    required_cols = ['district_code', 'year', 'month', 'add_outbreak', 'cholera_outbreak', 'typhoid_outbreak']
    
    # Add district name and state if available
    if 'district_name' in df.columns:
        required_cols.insert(1, 'district_name')
    if 'state_name' in df.columns or 'state' in df.columns:
        state_col = 'state_name' if 'state_name' in df.columns else 'state'
        df['state_name'] = df[state_col]
        required_cols.insert(2, 'state_name')
    
    # Filter to required columns
    available_cols = [col for col in required_cols if col in df.columns]
    df_filtered = df[available_cols].copy()
    
    # Aggregate: if any outbreak in district-month, mark as 1
    group_cols = [col for col in ['district_code', 'district_name', 'state_name', 'year', 'month'] if col in df_filtered.columns]
    
    df_aggregated = df_filtered.groupby(group_cols, as_index=False).agg({
        'add_outbreak': 'max',
        'cholera_outbreak': 'max',
        'typhoid_outbreak': 'max'
    })
    
    return df_aggregated

# Extract from EpiClim
epiclim_labels = extract_outbreak_labels(epiclim_df, "EpiClim")

if epiclim_labels is not None:
    print(f"  ✓ EpiClim: Extracted {len(epiclim_labels):,} district-month records")
    print(f"    ADD: {epiclim_labels['add_outbreak'].sum()}")
    print(f"    Cholera: {epiclim_labels['cholera_outbreak'].sum()}")
    print(f"    Typhoid: {epiclim_labels['typhoid_outbreak'].sum()}")
else:
    print(f"  ❌ Failed to extract EpiClim labels")
    exit(1)

# Extract from IDSP
if use_idsp:
    idsp_labels = extract_outbreak_labels(idsp_df, "IDSP")
    
    if idsp_labels is not None:
        print(f"  ✓ IDSP: Extracted {len(idsp_labels):,} district-month records")
        print(f"    ADD: {idsp_labels['add_outbreak'].sum()}")
        print(f"    Cholera: {idsp_labels['cholera_outbreak'].sum()}")
        print(f"    Typhoid: {idsp_labels['typhoid_outbreak'].sum()}")

# ============================================================================
# 6. MERGE DATASETS
# ============================================================================

print("\n🔗 Step 6: Merging outbreak datasets...")

if use_idsp and idsp_labels is not None:
    # Merge EpiClim and IDSP
    # Combine on district_code, year, month
    merge_cols = ['district_code', 'year', 'month']
    
    merged_labels = pd.concat([epiclim_labels, idsp_labels], ignore_index=True)
    
    # Aggregate again (in case of overlaps)
    group_cols = [col for col in ['district_code', 'district_name', 'state_name', 'year', 'month'] if col in merged_labels.columns]
    
    final_labels = merged_labels.groupby(group_cols, as_index=False).agg({
        'add_outbreak': 'max',
        'cholera_outbreak': 'max',
        'typhoid_outbreak': 'max'
    })
    
    print(f"  ✓ Merged datasets: {len(final_labels):,} unique district-month records")
else:
    final_labels = epiclim_labels
    print(f"  ✓ Using EpiClim only: {len(final_labels):,} records")

# ============================================================================
# 7. LOAD GEOJSON FOR DISTRICT NAME MAPPING (OPTIONAL)
# ============================================================================

print("\n🗺 Step 7: Loading district name mapping from GeoJSON...")

GEOJSON_PATH = "data/geo/india_districts.geojson"

if os.path.exists(GEOJSON_PATH):
    try:
        with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # Extract district code to name mapping
        district_mapping = {}
        for feature in geojson_data['features']:
            props = feature['properties']
            # Common property names
            code = props.get('dtcode') or props.get('district_code') or props.get('censuscode')
            name = props.get('district') or props.get('district_name') or props.get('DISTRICT')
            state = props.get('st_nm') or props.get('state_name') or props.get('STATE')
            
            if code:
                code_std = str(code).zfill(6)
                district_mapping[code_std] = {
                    'district_name': name,
                    'state_name': state
                }
        
        print(f"  ✓ Loaded {len(district_mapping)} districts from GeoJSON")
        
        # Fill missing district names
        missing_names = final_labels['district_name'].isna().sum() if 'district_name' in final_labels.columns else len(final_labels)
        
        if missing_names > 0:
            print(f"  Filling {missing_names} missing district names...")
            
            for idx, row in final_labels.iterrows():
                if pd.isna(row.get('district_name')) or pd.isna(row.get('state_name')):
                    mapping = district_mapping.get(row['district_code'])
                    if mapping:
                        if 'district_name' not in final_labels.columns or pd.isna(row.get('district_name')):
                            final_labels.at[idx, 'district_name'] = mapping['district_name']
                        if 'state_name' not in final_labels.columns or pd.isna(row.get('state_name')):
                            final_labels.at[idx, 'state_name'] = mapping['state_name']
            
            print(f"  ✓ Filled missing names")
    
    except Exception as e:
        print(f"  ⚠️ Failed to load GeoJSON: {e}")
else:
    print(f"  ⚠️ GeoJSON not found at {GEOJSON_PATH}")
    print(f"  Download from: https://github.com/datameet/maps")

# ============================================================================
# 8. SAVE FINAL OUTBREAK LABELS
# ============================================================================

print("\n💾 Step 8: Saving final outbreak labels...")

OUTPUT_PATH = "data/processed/outbreak_labels.csv"

# Ensure required columns exist
required_output_cols = ['district_code', 'year', 'month', 'add_outbreak', 'cholera_outbreak', 'typhoid_outbreak']

for col in required_output_cols:
    if col not in final_labels.columns:
        if col in ['add_outbreak', 'cholera_outbreak', 'typhoid_outbreak']:
            final_labels[col] = 0
        else:
            print(f"  ❌ Missing required column: {col}")
            exit(1)

# Add district_name and state_name if available
output_cols = ['district_code']
if 'district_name' in final_labels.columns:
    output_cols.append('district_name')
if 'state_name' in final_labels.columns:
    output_cols.append('state_name')
output_cols.extend(['year', 'month', 'add_outbreak', 'cholera_outbreak', 'typhoid_outbreak'])

final_labels = final_labels[output_cols].copy()

# Sort by district, year, month
final_labels = final_labels.sort_values(['district_code', 'year', 'month']).reset_index(drop=True)

# Save
final_labels.to_csv(OUTPUT_PATH, index=False)

print(f"  ✓ Saved to {OUTPUT_PATH}")
print(f"  Total records: {len(final_labels):,}")

# ============================================================================
# 9. SUMMARY STATISTICS
# ============================================================================

print("\n" + "=" * 70)
print("OUTBREAK DATA SUMMARY")
print("=" * 70)

print(f"\n📊 Dataset Coverage:")
print(f"  Total district-month records: {len(final_labels):,}")
print(f"  Unique districts: {final_labels['district_code'].nunique()}")
print(f"  Year range: {final_labels['year'].min()}-{final_labels['year'].max()}")

print(f"\n🦠 Outbreak Counts:")
print(f"  ADD outbreaks: {final_labels['add_outbreak'].sum():,} ({final_labels['add_outbreak'].mean()*100:.1f}%)")
print(f"  Cholera outbreaks: {final_labels['cholera_outbreak'].sum():,} ({final_labels['cholera_outbreak'].mean()*100:.1f}%)")
print(f"  Typhoid outbreaks: {final_labels['typhoid_outbreak'].sum():,} ({final_labels['typhoid_outbreak'].mean()*100:.1f}%)")

# Top 10 districts by outbreak count
print(f"\n🏆 Top 10 Districts by Total Outbreaks:")
final_labels['total_outbreaks'] = final_labels['add_outbreak'] + final_labels['cholera_outbreak'] + final_labels['typhoid_outbreak']
top_districts = final_labels.groupby('district_code')['total_outbreaks'].sum().sort_values(ascending=False).head(10)

for i, (district_code, count) in enumerate(top_districts.items(), 1):
    district_name = final_labels[final_labels['district_code'] == district_code]['district_name'].iloc[0] if 'district_name' in final_labels.columns else 'Unknown'
    print(f"  {i:2d}. {district_name} ({district_code}): {int(count)} outbreaks")

print("\n" + "=" * 70)
print("✅ OUTBREAK DATA INTEGRATION COMPLETE")
print("=" * 70)

print(f"\n🚀 NEXT STEPS:")
print(f"  1. Run: python src/build_district_filter.py")
print(f"  2. Run: python src/aws_pipeline.py")
print(f"  3. Run: python src/nasa_lst_pipeline.py")
print("=" * 70)
