"""
Download India Districts GeoJSON from GitHub
"""
import os
import requests

# Create directory
os.makedirs('data/geo', exist_ok=True)

# Download GeoJSON
url = 'https://raw.githubusercontent.com/geohacker/india/master/district/india_district.geojson'
print(f"Downloading India districts GeoJSON from {url}...")

try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    # Save file
    with open('data/geo/india_districts.geojson', 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print("✓ Successfully downloaded india_districts.geojson")
    print(f"  Saved to: data/geo/india_districts.geojson")
    print(f"  File size: {len(response.text) / 1024:.1f} KB")
    
except Exception as e:
    print(f"✗ Error downloading GeoJSON: {e}")
    print("\nAlternative: Download manually from:")
    print("https://github.com/datameet/maps/tree/master/Districts/Census_2011")
