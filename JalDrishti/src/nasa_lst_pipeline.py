"""
JalDrishti NASA MODIS LST Pipeline
Adds Land Surface Temperature data from MOD11A1 V061 to satellite indices
"""

import pandas as pd
import numpy as np
import earthaccess
import xarray as xr
import os
import time
from datetime import datetime

# Configuration
MAX_GRANULES = 3  # Maximum granules to download per district-month
LST_SCALE = 0.02  # Scale factor for MODIS LST
LST_OFFSET = -273.15  # Convert Kelvin to Celsius
FILL_VALUE_THRESHOLD = -100  # Mask values below this
SAVE_INTERVAL = 50  # Save progress every N rows

def authenticate_earthaccess():
    """Authenticate with NASA Earthdata"""
    
    print("\n🔐 Authenticating with NASA Earthdata...")
    print("  If this is your first time, you'll need to:")
    print("  1. Create account at: https://urs.earthdata.nasa.gov/")
    print("  2. Enter credentials when prompted")
    print()
    
    try:
        auth = earthaccess.login(strategy='interactive')
        
        if auth.authenticated:
            print("  ✓ Authentication successful")
            return auth
        else:
            print("  ❌ Authentication failed")
            return None
    
    except Exception as e:
        print(f"  ❌ Authentication error: {e}")
        return None


def get_lst_for_district_month(auth, bbox, year, month):
    """Download and process LST for a district-month"""
    
    try:
        # Format date range
        start_date = f"{year}-{month:02d}-01"
        
        # Calculate end date (last day of month)
        if month == 12:
            end_date = f"{year}-12-31"
        else:
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            end_date = f"{year}-{month:02d}-{last_day}"
        
        # Search for MOD11A1 V061 granules
        results = earthaccess.search_data(
            short_name='MOD11A1',
            version='061',
            bounding_box=bbox,
            temporal=(start_date, end_date),
            count=MAX_GRANULES
        )
        
        if len(results) == 0:
            return None
        
        # Download granules (to temp directory)
        files = earthaccess.download(results, local_path='data/temp/modis')
        
        if len(files) == 0:
            return None
        
        # Process LST from downloaded files
        lst_values = []
        
        for file in files:
            try:
                # Open with xarray
                ds = xr.open_dataset(file, engine='netcdf4')
                
                # Extract LST_Day_1km (daytime LST)
                if 'LST_Day_1km' in ds:
                    lst_data = ds['LST_Day_1km'].values
                elif 'LST_Night_1km' in ds:
                    lst_data = ds['LST_Night_1km'].values
                else:
                    # Try to find any LST variable
                    lst_vars = [v for v in ds.variables if 'LST' in v]
                    if len(lst_vars) > 0:
                        lst_data = ds[lst_vars[0]].values
                    else:
                        continue
                
                # Apply scale and offset
                lst_celsius = lst_data * LST_SCALE + LST_OFFSET
                
                # Mask fill values
                lst_celsius = np.where(lst_celsius < FILL_VALUE_THRESHOLD, np.nan, lst_celsius)
                
                # Calculate mean
                mean_lst = np.nanmean(lst_celsius)
                
                if not np.isnan(mean_lst):
                    lst_values.append(mean_lst)
                
                ds.close()
            
            except Exception as e:
                continue
        
        # Return mean of all granules
        if len(lst_values) > 0:
            return round(np.mean(lst_values), 2)
        else:
            return None
    
    except Exception as e:
        return None


def run_nasa_lst_pipeline():
    """Main LST pipeline function"""
    
    print("=" * 70)
    print("JalDrishti NASA MODIS LST Pipeline")
    print("=" * 70)
    
    # Authenticate
    auth = authenticate_earthaccess()
    
    if auth is None:
        print("\n❌ Cannot proceed without authentication")
        return
    
    # Load master satellite indices
    print("\n📊 Loading master satellite indices...")
    
    input_path = 'data/processed/master_satellite_indices.csv'
    
    if not os.path.exists(input_path):
        print(f"  ❌ {input_path} not found")
        print(f"  Run: python src/aws_pipeline.py")
        return
    
    df = pd.read_csv(input_path)
    df['district_code'] = df['district_code'].astype(str).str.zfill(6)
    
    print(f"  ✓ Loaded {len(df)} rows")
    
    # Check for existing LST values
    if 'lst_celsius' not in df.columns:
        df['lst_celsius'] = None
    
    # Count rows needing LST
    missing_lst = df['lst_celsius'].isna().sum()
    
    print(f"  Rows with LST: {len(df) - missing_lst}")
    print(f"  Rows needing LST: {missing_lst}")
    
    if missing_lst == 0:
        print(f"\n✅ All rows already have LST data!")
        return
    
    # Load district bounding boxes
    print("\n🗺 Loading district bounding boxes...")
    
    geojson_path = 'data/geo/india_districts.geojson'
    
    if not os.path.exists(geojson_path):
        print(f"  ❌ {geojson_path} not found")
        print(f"  Download from: https://github.com/datameet/maps")
        return
    
    import json
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    district_bboxes = {}
    
    for feature in geojson_data['features']:
        props = feature['properties']
        geom = feature['geometry']
        
        code = props.get('dtcode') or props.get('district_code') or props.get('censuscode')
        if not code:
            continue
        
        code_std = str(code).zfill(6)
        
        # Calculate bounding box
        if geom['type'] == 'Polygon':
            coords = geom['coordinates'][0]
        elif geom['type'] == 'MultiPolygon':
            coords = []
            for polygon in geom['coordinates']:
                coords.extend(polygon[0])
        else:
            continue
        
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        
        # MODIS bbox format: (lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat)
        bbox = (min(lons), min(lats), max(lons), max(lats))
        
        district_bboxes[code_std] = bbox
    
    print(f"  ✓ Loaded {len(district_bboxes)} district bounding boxes")
    
    # Create temp directory
    os.makedirs('data/temp/modis', exist_ok=True)
    
    # Process rows needing LST
    print(f"\n🔄 Processing {missing_lst} rows...")
    print(f"  Saving progress every {SAVE_INTERVAL} rows")
    
    processed_count = 0
    failed_count = 0
    save_counter = 0
    start_time = time.time()
    
    for idx, row in df[df['lst_celsius'].isna()].iterrows():
        district_code = row['district_code']
        district_name = row['district_name']
        year = row['year']
        month = row['month']
        
        # Progress indicator
        processed_count += 1
        
        if processed_count % 10 == 0 or processed_count == 1:
            elapsed = time.time() - start_time
            rate = processed_count / elapsed if elapsed > 0 else 0
            eta = (missing_lst - processed_count) / rate if rate > 0 else 0
            
            print(f"\n  [{processed_count}/{missing_lst}] {district_name}, {year}-{month:02d}")
            print(f"    Progress: {processed_count/missing_lst*100:.1f}% | Rate: {rate*60:.1f} rows/min | ETA: {eta/60:.1f} min")
        
        # Get bbox
        if district_code not in district_bboxes:
            print(f"    ⚠️ No bbox found for {district_code}")
            failed_count += 1
            continue
        
        bbox = district_bboxes[district_code]
        
        # Get LST
        lst = get_lst_for_district_month(auth, bbox, year, month)
        
        if lst is not None:
            df.at[idx, 'lst_celsius'] = lst
            save_counter += 1
        else:
            failed_count += 1
        
        # Save progress periodically
        if save_counter >= SAVE_INTERVAL:
            print(f"\n  💾 Saving progress ({save_counter} new LST values)...")
            df.to_csv(input_path, index=False)
            print(f"    ✓ Saved to {input_path}")
            save_counter = 0
    
    # Final save
    if save_counter > 0:
        print(f"\n💾 Final save ({save_counter} new LST values)...")
        df.to_csv(input_path, index=False)
        print(f"  ✓ Saved to {input_path}")
    
    # Summary
    elapsed_total = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("NASA LST PIPELINE COMPLETE")
    print("=" * 70)
    
    print(f"\n📊 Processing Summary:")
    print(f"  Total rows processed: {processed_count}")
    print(f"  Successfully added LST: {processed_count - failed_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Success rate: {(processed_count - failed_count)/processed_count*100:.1f}%")
    print(f"  Total time: {elapsed_total/60:.1f} minutes")
    
    # Check final coverage
    final_missing = df['lst_celsius'].isna().sum()
    
    print(f"\n📁 Output:")
    print(f"  File: {input_path}")
    print(f"  Total rows: {len(df):,}")
    print(f"  Rows with LST: {len(df) - final_missing:,} ({(len(df) - final_missing)/len(df)*100:.1f}%)")
    print(f"  Rows missing LST: {final_missing:,}")
    
    if final_missing > 0:
        print(f"\n  ⚠️ Some rows still missing LST (likely no MODIS coverage)")
        print(f"  Consider filling with interpolation or regional averages")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"  1. Run: python src/feature_engineering.py")
    print(f"  2. Run: python src/model_trainer.py")
    print("=" * 70)


if __name__ == "__main__":
    run_nasa_lst_pipeline()
