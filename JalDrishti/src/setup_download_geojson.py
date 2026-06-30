"""
Step 5: Download India district boundary GeoJSON and extract property keys.
"""
import requests
import json
from pathlib import Path

OUT_PATH   = Path("data/geo/india_districts.geojson")
KEYS_PATH  = Path("config/geojson_property_keys.json")

PRIMARY  = "https://raw.githubusercontent.com/geohacker/india/master/district/india_district.geojson"
FALLBACK = "https://raw.githubusercontent.com/datameet/maps/master/Country/india-composite.geojson"

def download_geojson():
    print("=== GeoJSON Download ===")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    for label, url in [("PRIMARY", PRIMARY), ("FALLBACK", FALLBACK)]:
        print(f"  Trying {label}: {url}")
        try:
            r = requests.get(url, timeout=120, stream=True)
            r.raise_for_status()
            with open(OUT_PATH, "wb") as fh:
                for chunk in r.iter_content(chunk_size=65536):
                    fh.write(chunk)
            file_size = OUT_PATH.stat().st_size
            print(f"  Downloaded {file_size:,} bytes to {OUT_PATH}")
            break
        except Exception as e:
            print(f"  {label} FAILED: {e}")
            if label == "FALLBACK":
                print("  STATUS: FAIL — both sources failed")
                return False

    # Verify and extract property keys
    try:
        with open(OUT_PATH, "r", encoding="utf-8") as fh:
            geo = json.load(fh)
        features = geo.get("features", [])
        print(f"  Features (districts) found: {len(features)}")

        if features:
            props = features[0]["properties"]
            print(f"  First feature properties: {props}")

            # Identify the correct keys
            all_keys = list(props.keys())
            name_key = next((k for k in all_keys if "name" in k.lower() or "dist" in k.lower()), all_keys[0])
            state_key = next((k for k in all_keys if "state" in k.lower() or "st_" in k.lower()), None)
            code_key = next((k for k in all_keys if "code" in k.lower() or "dt_" in k.lower()), None)

            key_config = {
                "district_name_key": name_key,
                "state_name_key": state_key,
                "district_code_key": code_key,
                "all_property_keys": all_keys
            }
            KEYS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(KEYS_PATH, "w") as fh:
                json.dump(key_config, fh, indent=2)
            print(f"  Property keys saved to {KEYS_PATH}")
            print(f"  district_name_key = '{name_key}'")
            print(f"  state_name_key    = '{state_key}'")
            print(f"  district_code_key = '{code_key}'")

        print("  STATUS: PASS")
        return True
    except Exception as e:
        print(f"  FAILED to parse GeoJSON: {e}")
        return False

if __name__ == "__main__":
    download_geojson()
