"""
JalDrishti Mock Data Generator
Generates realistic mock satellite, SVI, and outbreak data for development and testing.
Run this FIRST to unblock all other development.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

# Set random seed for reproducibility
np.random.seed(42)

# Create output directory
os.makedirs('data/processed', exist_ok=True)

print("=" * 70)
print("JalDrishti Mock Data Generator v5.0")
print("=" * 70)

# Define 10 fallback test districts
FALLBACK_DISTRICTS = [
    {'district_code': '101001', 'district_name': 'Patna', 'state_name': 'Bihar'},
    {'district_code': '090001', 'district_name': 'Varanasi', 'state_name': 'Uttar Pradesh'},
    {'district_code': '190001', 'district_name': 'Malda', 'state_name': 'West Bengal'},
    {'district_code': '210001', 'district_name': 'Puri', 'state_name': 'Odisha'},
    {'district_code': '180001', 'district_name': 'Kamrup', 'state_name': 'Assam'},
    {'district_code': '320001', 'district_name': 'Alappuzha', 'state_name': 'Kerala'},
    {'district_code': '270001', 'district_name': 'Nandurbar', 'state_name': 'Maharashtra'},
    {'district_code': '080001', 'district_name': 'Jaipur', 'state_name': 'Rajasthan'},
    {'district_code': '101002', 'district_name': 'Muzaffarpur', 'state_name': 'Bihar'},
    {'district_code': '190002', 'district_name': 'Murshidabad', 'state_name': 'West Bengal'},
]

# Try to load valid districts, fall back to test districts
try:
    valid_districts_df = pd.read_csv('data/processed/valid_districts.csv')
    districts = valid_districts_df.to_dict('records')
    print(f"✓ Loaded {len(districts)} districts from valid_districts.csv")
except FileNotFoundError:
    districts = FALLBACK_DISTRICTS
    print(f"⚠ valid_districts.csv not found. Using {len(districts)} fallback test districts.")
    print("  Run build_district_filter.py after downloading real data to use actual districts.")

# Generate time range: 2019-2023 (5 years × 12 months = 60 rows per district)
years = range(2019, 2024)
months = range(1, 13)

print(f"\n📅 Generating data for {len(years)} years × {len(months)} months = {len(years) * len(months)} rows per district")

# ============================================================================
# 1. SATELLITE INDICES CSV
# ============================================================================
print("\n🛰 Generating master_satellite_indices.csv...")

satellite_data = []

for district in districts:
    district_code = district['district_code']
    district_name = district['district_name']
    state_name = district['state_name']
    
    for year in years:
        for month in months:
            # Monsoon seasonality (June-September have elevated values)
            is_monsoon = 1 if month in [6, 7, 8, 9] else 0
            monsoon_boost = 0.3 if is_monsoon else 0.0
            
            # Generate satellite indices with realistic patterns
            turbidity = np.clip(np.random.normal(0.10 + monsoon_boost * 0.15, 0.05), 0, 1)
            ndci = np.clip(np.random.normal(0.05 + monsoon_boost * 0.08, 0.03), -1, 1)
            cdom = np.clip(np.random.normal(0.60 + monsoon_boost * 0.20, 0.15), 0, 2)
            ndwi = np.clip(np.random.normal(-0.10 + monsoon_boost * 0.25, 0.08), -1, 1)
            awei = np.clip(np.random.normal(-0.20 + monsoon_boost * 0.30, 0.10), -1, 1)
            lst_celsius = np.clip(np.random.normal(28 + monsoon_boost * 4, 3), 10, 45)
            
            satellite_data.append({
                'district_code': district_code,
                'district_name': district_name,
                'state_name': state_name,
                'year': year,
                'month': month,
                'turbidity': round(turbidity, 4),
                'ndci': round(ndci, 4),
                'cdom': round(cdom, 4),
                'ndwi': round(ndwi, 4),
                'awei': round(awei, 4),
                'lst_celsius': round(lst_celsius, 2)
            })

satellite_df = pd.DataFrame(satellite_data)
satellite_df.to_csv('data/processed/master_satellite_indices.csv', index=False)
print(f"✓ Generated {len(satellite_df)} rows → data/processed/master_satellite_indices.csv")
print(f"  Columns: {list(satellite_df.columns)}")

# ============================================================================
# 2. SVI SCORES CSV
# ============================================================================
print("\n🏘 Generating district_svi_scores.csv...")

svi_data = []

for district in districts:
    # Generate plausible SVI with geographic patterns
    # Bihar/UP/WB tend higher vulnerability, Kerala/Himachal lower
    base_svi = 0.5
    
    if district['state_name'] in ['Bihar', 'Uttar Pradesh', 'West Bengal', 'Jharkhand']:
        base_svi = 0.65
    elif district['state_name'] in ['Kerala', 'Himachal Pradesh', 'Goa']:
        base_svi = 0.35
    
    svi_score = np.clip(np.random.normal(base_svi, 0.15), 0.2, 0.9)
    
    svi_data.append({
        'district_code': district['district_code'],
        'district_name': district['district_name'],
        'state_name': district['state_name'],
        'svi_score': round(svi_score, 4)
    })

svi_df = pd.DataFrame(svi_data)
svi_df.to_csv('data/processed/district_svi_scores.csv', index=False)
print(f"✓ Generated {len(svi_df)} rows → data/processed/district_svi_scores.csv")

# ============================================================================
# 3. OUTBREAK LABELS CSV
# ============================================================================
print("\n🦠 Generating outbreak_labels.csv...")

outbreak_data = []

for district in districts:
    district_code = district['district_code']
    district_name = district['district_name']
    state_name = district['state_name']
    
    for year in years:
        for month in months:
            # Monsoon-elevated outbreak probabilities
            is_monsoon = 1 if month in [6, 7, 8, 9] else 0
            
            # ADD: 12% monsoon / 3% other
            add_prob = 0.12 if is_monsoon else 0.03
            add_outbreak = 1 if np.random.random() < add_prob else 0
            
            # Cholera: 8% monsoon / 2% other
            cholera_prob = 0.08 if is_monsoon else 0.02
            cholera_outbreak = 1 if np.random.random() < cholera_prob else 0
            
            # Typhoid: 6% monsoon / 4% other (less seasonal)
            typhoid_prob = 0.06 if is_monsoon else 0.04
            typhoid_outbreak = 1 if np.random.random() < typhoid_prob else 0
            
            outbreak_data.append({
                'district_code': district_code,
                'district_name': district_name,
                'state_name': state_name,
                'year': year,
                'month': month,
                'add_outbreak': add_outbreak,
                'cholera_outbreak': cholera_outbreak,
                'typhoid_outbreak': typhoid_outbreak
            })

outbreak_df = pd.DataFrame(outbreak_data)
outbreak_df.to_csv('data/processed/outbreak_labels.csv', index=False)
print(f"✓ Generated {len(outbreak_df)} rows → data/processed/outbreak_labels.csv")
print(f"  ADD outbreaks: {outbreak_df['add_outbreak'].sum()}")
print(f"  Cholera outbreaks: {outbreak_df['cholera_outbreak'].sum()}")
print(f"  Typhoid outbreaks: {outbreak_df['typhoid_outbreak'].sum()}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("✅ MOCK DATA GENERATION COMPLETE")
print("=" * 70)
print(f"\nGenerated 3 files in data/processed/:")
print(f"  1. master_satellite_indices.csv  ({len(satellite_df):,} rows)")
print(f"  2. district_svi_scores.csv       ({len(svi_df):,} rows)")
print(f"  3. outbreak_labels.csv           ({len(outbreak_df):,} rows)")
print(f"\n📊 Data coverage:")
print(f"  Districts: {len(districts)}")
print(f"  Time range: 2019-2023 (5 years)")
print(f"  Total district-months: {len(satellite_df):,}")
print(f"\n🚀 NEXT STEPS:")
print(f"  1. Run: python src/feature_engineering.py")
print(f"  2. Run: python src/model_trainer.py")
print(f"  3. Run: streamlit run dashboard/app.py")
print(f"\n💡 To use real data instead of mock:")
print(f"  1. Download EpiClim + IDSP data to data/raw/")
print(f"  2. Run: python src/build_district_filter.py")
print(f"  3. Run: python src/aws_pipeline.py")
print(f"  4. Run: python src/nasa_lst_pipeline.py")
print("=" * 70)
