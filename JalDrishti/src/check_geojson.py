"""Check GeoJSON properties and update dashboard if needed"""
import json
import os

os.chdir('JalDrishti')

print("Checking GeoJSON file...")
print("=" * 60)

try:
    with open('data/geo/india_districts.geojson', 'r', encoding='utf-8') as f:
        geo = json.load(f)
    
    print(f"✓ GeoJSON file found!")
    print(f"  Total features: {len(geo['features'])}")
    print()
    
    # Check first feature properties
    if len(geo['features']) > 0:
        props = geo['features'][0]['properties']
        print("Property names in GeoJSON:")
        print("-" * 60)
        for key, value in props.items():
            print(f"  {key:20s} = {value}")
        print()
        
        # Check if district code exists
        has_dtcode = 'dtcode' in props
        has_district_code = 'district_code' in props
        has_id = 'ID_2' in props or 'id' in props
        
        print("Dashboard compatibility:")
        print("-" * 60)
        if has_dtcode:
            print("  ✓ 'dtcode' property found - Dashboard will work!")
        elif has_district_code:
            print("  ✓ 'district_code' property found - Dashboard will work!")
        else:
            print("  ⚠ No 'dtcode' or 'district_code' property found")
            print("  ℹ Dashboard will show table view instead of map")
            print()
            print("  Available properties that might be district identifiers:")
            for key in props.keys():
                if 'id' in key.lower() or 'code' in key.lower() or 'name' in key.lower():
                    print(f"    - {key}")
        
except FileNotFoundError:
    print("✗ GeoJSON file not found at: data/geo/india_districts.geojson")
except Exception as e:
    print(f"✗ Error reading GeoJSON: {e}")

print()
print("=" * 60)
