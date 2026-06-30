"""
JalDrishti AWS Earth Search Test Script
Single-district test for Patna, June 2022
Tests Sentinel-2 L2A data access and index calculation
"""

import numpy as np
from pystac_client import Client
import odc.stac
from dask.distributed import Client as DaskClient
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("JalDrishti AWS Earth Search Test - Patna, June 2022")
print("=" * 70)

# Start Dask client for memory management
print("\n🚀 Starting Dask client...")
dask_client = DaskClient(n_workers=2, threads_per_worker=2, memory_limit='2GB')
print(f"  ✓ Dask dashboard: {dask_client.dashboard_link}")

# Configure rioxarray for cloud-optimized access
print("\n☁️ Configuring cloud access...")
import rioxarray
rioxarray.set_options(cloud_defaults=True)

# Test parameters
BBOX = [84.9, 25.3, 85.4, 25.8]  # Patna bounding box
DATE_RANGE = "2022-06/2022-06"
CLOUD_THRESHOLD = 40

print(f"\n📍 Test Parameters:")
print(f"  Location: Patna, Bihar")
print(f"  Bounding Box: {BBOX}")
print(f"  Date Range: {DATE_RANGE}")
print(f"  Cloud Threshold: <{CLOUD_THRESHOLD}%")

# Connect to AWS Earth Search
print(f"\n🔗 Connecting to AWS Earth Search...")
catalog = Client.open("https://earth-search.aws.element84.com/v1")
print(f"  ✓ Connected to catalog")

# Search for Sentinel-2 L2A scenes
print(f"\n🔍 Searching for Sentinel-2 L2A scenes...")
search = catalog.search(
    collections=["sentinel-2-l2a"],  # CRITICAL: Use sentinel-2-l2a NOT sentinel-2-c1-l2a
    bbox=BBOX,
    datetime=DATE_RANGE,
    query={"eo:cloud_cover": {"lt": CLOUD_THRESHOLD}}
)

items = list(search.items())
print(f"  ✓ Found {len(items)} scenes")

if len(items) == 0:
    print(f"\n⚠️ No scenes found with cloud cover <{CLOUD_THRESHOLD}%")
    print(f"  Try increasing cloud threshold to 60 or 80")
    print(f"  Or try a different month")
    dask_client.close()
    exit(0)

# Load data
print(f"\n📥 Loading satellite data...")
print(f"  Bands: B03 (Green), B04 (Red), B05 (Red Edge), B08 (NIR), B11 (SWIR1), B12 (SWIR2)")

try:
    data = odc.stac.load(
        items,
        bands=['B03', 'B04', 'B05', 'B08', 'B11', 'B12'],
        bbox=BBOX,
        resolution=100,  # 100m resolution to prevent RAM crash
        chunks={'x': 512, 'y': 512},
        groupby='solar_day'
    )
    
    print(f"  ✓ Loaded data shape: {data.dims}")
    
    # Compute monthly median composite
    print(f"\n📊 Computing monthly median composite...")
    composite = data.median(dim='time').compute()
    print(f"  ✓ Composite computed")
    
    # Calculate water quality indices
    print(f"\n🧪 Calculating water quality indices...")
    
    # Extract bands
    B03 = composite['B03'].values.astype(float)
    B04 = composite['B04'].values.astype(float)
    B05 = composite['B05'].values.astype(float)
    B08 = composite['B08'].values.astype(float)
    B11 = composite['B11'].values.astype(float)
    B12 = composite['B12'].values.astype(float)
    
    # Turbidity Index
    turbidity = np.nanmedian((B04 - B03) / (B04 + B03 + 1e-10))
    
    # NDCI (Normalized Difference Chlorophyll Index)
    ndci = np.nanmedian((B05 - B04) / (B05 + B04 + 1e-10))
    
    # CDOM (Colored Dissolved Organic Matter)
    cdom = np.nanmedian(B03 / (B04 + 1e-10))
    
    # NDWI (Normalized Difference Water Index)
    ndwi = np.nanmedian((B03 - B08) / (B03 + B08 + 1e-10))
    
    # AWEI (Automated Water Extraction Index)
    awei = np.nanmedian(4 * (B03 - B11) - 0.25 * B08 + 2.75 * B12)
    
    # Print results
    print(f"\n✅ WATER QUALITY INDICES:")
    print(f"  Turbidity: {turbidity:.4f}")
    print(f"  NDCI: {ndci:.4f}")
    print(f"  CDOM: {cdom:.4f}")
    print(f"  NDWI: {ndwi:.4f}")
    print(f"  AWEI: {awei:.4f}")
    
    print(f"\n" + "=" * 70)
    print("✅ TEST PASSED — AWS pipeline working!")
    print("=" * 70)
    print(f"\n🚀 NEXT STEPS:")
    print(f"  1. Run full pipeline: python src/aws_pipeline.py")
    print(f"  2. Add LST data: python src/nasa_lst_pipeline.py")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print(f"\nTroubleshooting:")
    print(f"  1. Check internet connection")
    print(f"  2. Try increasing cloud threshold to 60")
    print(f"  3. Try a different month (monsoon months have more clouds)")

finally:
    dask_client.close()
    print(f"\n🔒 Dask client closed")
