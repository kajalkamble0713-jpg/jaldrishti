"""
JalDrishti AWS Earth Search Production Pipeline
Processes all valid districts for 2019-2023 with resume capability
"""

import numpy as np
import pandas as pd
from pystac_client import Client
import odc.stac
from dask.distributed import Client as DaskClient
import warnings
import json
import os
from datetime import datetime
import time

warnings.filterwarnings('ignore')

# Configuration
BBOX_BUFFER = 0.1  # Degrees to expand bounding box
CLOUD_THRESHOLD_NORMAL = 40
CLOUD_THRESHOLD_MONSOON = 60
RESOLUTION = 100  # meters
CHUNK_SIZE = 512
SAVE_INTERVAL = 50  # Save progress every N rows
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def load_district_bboxes(geojson_path='data/geo/india_districts.geojson'):
    """Load district bounding boxes from GeoJSON"""
    
    if not os.path.exists(geojson_path):
        print(f"  ⚠️ GeoJSON not found at {geojson_path}")
        print(f"  Download from: https://github.com/datameet/maps")
        return None
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    district_bboxes = {}
    
    for feature in geojson_data['features']:
        props = feature['properties']
        geom = feature['geometry']
        
        # Extract district code
        code = props.get('dtcode') or props.get('district_code') or props.get('censuscode')
        if not code:
            continue
        
        code_std = str(code).zfill(6)
        
        # Calculate bounding box from geometry
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
        
        bbox = [
            min(lons) - BBOX_BUFFER,
            min(lats) - BBOX_BUFFER,
            max(lons) + BBOX_BUFFER,
            max(lats) + BBOX_BUFFER
        ]
        
        district_bboxes[code_std] = bbox
    
    return district_bboxes


def calculate_satellite_indices(data):
    """Calculate water quality indices from Sentinel-2 bands"""
    
    # Extract bands
    B03 = data['B03'].values.astype(float)
    B04 = data['B04'].values.astype(float)
    B05 = data['B05'].values.astype(float)
    B08 = data['B08'].values.astype(float)
    B11 = data['B11'].values.astype(float)
    B12 = data['B12'].values.astype(float)
    
    # Calculate indices
    indices = {}
    
    # Turbidity Index
    indices['turbidity'] = np.nanmedian((B04 - B03) / (B04 + B03 + 1e-10))
    
    # NDCI (Normalized Difference Chlorophyll Index)
    indices['ndci'] = np.nanmedian((B05 - B04) / (B05 + B04 + 1e-10))
    
    # CDOM (Colored Dissolved Organic Matter)
    indices['cdom'] = np.nanmedian(B03 / (B04 + 1e-10))
    
    # NDWI (Normalized Difference Water Index)
    indices['ndwi'] = np.nanmedian((B03 - B08) / (B03 + B08 + 1e-10))
    
    # AWEI (Automated Water Extraction Index)
    indices['awei'] = np.nanmedian(4 * (B03 - B11) - 0.25 * B08 + 2.75 * B12)
    
    return indices


def process_district_month(catalog, district_code, district_name, state_name, bbox, year, month, dask_client):
    """Process a single district-month combination"""
    
    # Determine cloud threshold based on monsoon season
    is_monsoon = month in [6, 7, 8, 9]
    cloud_threshold = CLOUD_THRESHOLD_MONSOON if is_monsoon else CLOUD_THRESHOLD_NORMAL
    
    # Format date range
    date_range = f"{year}-{month:02d}/{year}-{month:02d}"
    
    try:
        # Search for Sentinel-2 L2A scenes
        search = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=bbox,
            datetime=date_range,
            query={"eo:cloud_cover": {"lt": cloud_threshold}}
        )
        
        items = list(search.items())
        
        if len(items) == 0:
            # No scenes found
            return None
        
        # Load data
        data = odc.stac.load(
            items,
            bands=['B03', 'B04', 'B05', 'B08', 'B11', 'B12'],
            bbox=bbox,
            resolution=RESOLUTION,
            chunks={'x': CHUNK_SIZE, 'y': CHUNK_SIZE},
            groupby='solar_day'
        )
        
        # Compute monthly median composite
        composite = data.median(dim='time').compute()
        
        # Calculate indices
        indices = calculate_satellite_indices(composite)
        
        # Create result row
        result = {
            'district_code': district_code,
            'district_name': district_name,
            'state_name': state_name,
            'year': year,
            'month': month,
            'turbidity': round(indices['turbidity'], 4),
            'ndci': round(indices['ndci'], 4),
            'cdom': round(indices['cdom'], 4),
            'ndwi': round(indices['ndwi'], 4),
            'awei': round(indices['awei'], 4),
            'lst_celsius': None  # Will be filled by NASA pipeline
        }
        
        return result
    
    except Exception as e:
        print(f"    ❌ Error: {str(e)[:100]}")
        return None


def run_aws_pipeline():
    """Main pipeline function"""
    
    print("=" * 70)
    print("JalDrishti AWS Earth Search Production Pipeline")
    print("=" * 70)
    
    # Start Dask client
    print("\n🚀 Starting Dask client...")
    dask_client = DaskClient(n_workers=2, threads_per_worker=2, memory_limit='2GB')
    print(f"  ✓ Dask dashboard: {dask_client.dashboard_link}")
    
    # Configure rioxarray
    print("\n☁️ Configuring cloud access...")
    import rioxarray
    rioxarray.set_options(cloud_defaults=True)
    
    # Load valid districts
    print("\n📊 Loading valid districts...")
    
    valid_districts_path = 'data/processed/valid_districts.csv'
    
    if not os.path.exists(valid_districts_path):
        print(f"  ❌ {valid_districts_path} not found")
        print(f"  Run: python src/build_district_filter.py")
        dask_client.close()
        return
    
    valid_districts_df = pd.read_csv(valid_districts_path)
    valid_districts_df['district_code'] = valid_districts_df['district_code'].astype(str).str.zfill(6)
    
    print(f"  ✓ Loaded {len(valid_districts_df)} valid districts")
    
    # Load district bounding boxes
    print("\n🗺 Loading district bounding boxes...")
    district_bboxes = load_district_bboxes()
    
    if district_bboxes is None:
        print(f"  ❌ Cannot proceed without bounding boxes")
        dask_client.close()
        return
    
    print(f"  ✓ Loaded {len(district_bboxes)} district bounding boxes")
    
    # Load existing data for resume capability
    output_path = 'data/processed/master_satellite_indices.csv'
    
    if os.path.exists(output_path):
        print(f"\n📂 Found existing data at {output_path}")
        existing_df = pd.read_csv(output_path)
        existing_df['district_code'] = existing_df['district_code'].astype(str).str.zfill(6)
        
        # Create set of processed combinations
        processed_set = set(
            zip(existing_df['district_code'], existing_df['year'], existing_df['month'])
        )
        
        print(f"  ✓ Loaded {len(existing_df)} existing rows")
        print(f"  Resume mode: Will skip {len(processed_set)} already-processed district-months")
    else:
        existing_df = pd.DataFrame()
        processed_set = set()
        print(f"\n📂 No existing data found. Starting fresh.")
    
    # Connect to AWS Earth Search
    print(f"\n🔗 Connecting to AWS Earth Search...")
    catalog = Client.open("https://earth-search.aws.element84.com/v1")
    print(f"  ✓ Connected")
    
    # Generate task list
    print(f"\n📋 Generating task list...")
    
    tasks = []
    years = range(2019, 2024)
    months = range(1, 13)
    
    for _, district_row in valid_districts_df.iterrows():
        district_code = district_row['district_code']
        district_name = district_row['district_name']
        state_name = district_row['state_name']
        
        # Check if bbox exists
        if district_code not in district_bboxes:
            continue
        
        bbox = district_bboxes[district_code]
        
        for year in years:
            for month in months:
                # Skip if already processed
                if (district_code, year, month) in processed_set:
                    continue
                
                tasks.append({
                    'district_code': district_code,
                    'district_name': district_name,
                    'state_name': state_name,
                    'bbox': bbox,
                    'year': year,
                    'month': month
                })
    
    total_tasks = len(tasks)
    print(f"  ✓ Generated {total_tasks} tasks")
    
    if total_tasks == 0:
        print(f"\n✅ All district-months already processed!")
        dask_client.close()
        return
    
    # Process tasks
    print(f"\n🔄 Processing {total_tasks} district-months...")
    print(f"  Saving progress every {SAVE_INTERVAL} rows")
    
    results = []
    processed_count = 0
    failed_count = 0
    start_time = time.time()
    
    for i, task in enumerate(tasks, 1):
        district_code = task['district_code']
        district_name = task['district_name']
        state_name = task['state_name']
        bbox = task['bbox']
        year = task['year']
        month = task['month']
        
        # Progress indicator
        if i % 10 == 0 or i == 1:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            eta = (total_tasks - i) / rate if rate > 0 else 0
            
            print(f"\n  [{i}/{total_tasks}] {district_name}, {year}-{month:02d}")
            print(f"    Progress: {i/total_tasks*100:.1f}% | Rate: {rate:.1f} tasks/min | ETA: {eta/60:.1f} min")
        
        # Process with retries
        result = None
        for attempt in range(MAX_RETRIES):
            try:
                result = process_district_month(
                    catalog, district_code, district_name, state_name,
                    bbox, year, month, dask_client
                )
                break
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"    ⚠️ Attempt {attempt+1} failed, retrying in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"    ❌ All retries failed")
        
        if result is not None:
            results.append(result)
            processed_count += 1
        else:
            failed_count += 1
        
        # Save progress periodically
        if len(results) >= SAVE_INTERVAL:
            print(f"\n  💾 Saving progress ({len(results)} new rows)...")
            
            new_df = pd.DataFrame(results)
            
            if len(existing_df) > 0:
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                combined_df = new_df
            
            combined_df.to_csv(output_path, index=False)
            print(f"    ✓ Saved to {output_path} ({len(combined_df)} total rows)")
            
            # Update existing_df and clear results
            existing_df = combined_df
            results = []
    
    # Final save
    if len(results) > 0:
        print(f"\n💾 Final save ({len(results)} new rows)...")
        
        new_df = pd.DataFrame(results)
        
        if len(existing_df) > 0:
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df
        
        combined_df.to_csv(output_path, index=False)
        print(f"  ✓ Saved to {output_path} ({len(combined_df)} total rows)")
    
    # Close Dask client
    dask_client.close()
    
    # Summary
    elapsed_total = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("AWS PIPELINE COMPLETE")
    print("=" * 70)
    
    print(f"\n📊 Processing Summary:")
    print(f"  Total tasks: {total_tasks}")
    print(f"  Successfully processed: {processed_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Success rate: {processed_count/total_tasks*100:.1f}%")
    print(f"  Total time: {elapsed_total/60:.1f} minutes")
    print(f"  Average rate: {total_tasks/(elapsed_total/60):.1f} tasks/min")
    
    print(f"\n📁 Output:")
    print(f"  File: {output_path}")
    
    if os.path.exists(output_path):
        final_df = pd.read_csv(output_path)
        print(f"  Total rows: {len(final_df):,}")
        print(f"  Districts: {final_df['district_code'].nunique()}")
        print(f"  Year range: {final_df['year'].min()}-{final_df['year'].max()}")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"  1. Run: python src/nasa_lst_pipeline.py")
    print(f"  2. Run: python src/feature_engineering.py")
    print("=" * 70)


if __name__ == "__main__":
    run_aws_pipeline()
