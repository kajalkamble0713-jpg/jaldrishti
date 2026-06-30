"""
Check GeoJSON property names
"""
import json

with open('data/geo/india_districts.geojson', 'r', encoding='utf-8') as f:
    geo = json.load(f)

print("GeoJSON Properties:")
print("=" * 50)
if 'features' in geo and len(geo['features']) > 0:
    props = geo['features'][0]['properties']
    for key, value in props.items():
        print(f"  {key}: {value}")
else:
    print("No features found in GeoJSON")
