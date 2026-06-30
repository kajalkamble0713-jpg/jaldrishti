"""
Phase 2 Step 2 — Geospatial Setup
Usage: python src/prepare_geo.py
Output: data/processed/district_centroids_v2.csv
"""
import json, pandas as pd, math
from pathlib import Path

BASE     = Path(__file__).parent.parent
GEO_PATH = BASE / "data/geo/india_districts.geojson"
CFG_PATH = BASE / "config/geojson_property_keys.json"
LABELS   = BASE / "data/processed/epiclim_labels.csv"
OUT      = BASE / "data/processed/district_centroids_v2.csv"

def centroid_of_polygon(coords):
    """Compute centroid of a polygon (list of [lon,lat] pairs)."""
    xs = [p[0] for p in coords if isinstance(p, (list,tuple)) and len(p)==2]
    ys = [p[1] for p in coords if isinstance(p, (list,tuple)) and len(p)==2]
    if not xs: return None, None
    return sum(xs)/len(xs), sum(ys)/len(ys)

def get_geom_centroid(geometry):
    gtype = geometry.get("type","")
    coords = geometry.get("coordinates",[])
    try:
        if gtype == "Polygon":
            return centroid_of_polygon(coords[0])
        elif gtype == "MultiPolygon":
            # Use largest polygon
            polys = [(len(p[0]), p[0]) for p in coords]
            polys.sort(reverse=True)
            return centroid_of_polygon(polys[0][1])
    except:
        pass
    return None, None

print("=== prepare_geo.py ===")

# Load config
with open(CFG_PATH) as f:
    cfg = json.load(f)
name_key  = cfg.get("district_name_key","NAME_2")
state_key = cfg.get("state_name_key","NAME_1")
print(f"Using keys: district='{name_key}', state='{state_key}'")

# Load GeoJSON
with open(GEO_PATH) as f:
    geo = json.load(f)
features = geo["features"]
print(f"GeoJSON features: {len(features)}")

# Build centroids
rows = []
for feat in features:
    props = feat.get("properties", {})
    geom  = feat.get("geometry", {})
    dname = str(props.get(name_key, "") or "").strip()
    sname = str(props.get(state_key,"") or "").strip()
    if not dname:
        continue
    lon, lat = get_geom_centroid(geom)
    if lat is None:
        continue
    rows.append({"district_name": dname, "state_name": sname,
                 "lat": round(lat,5), "lon": round(lon,5)})

centroids_df = pd.DataFrame(rows)
print(f"Centroids computed: {len(centroids_df)}")

# Cross-reference with epiclim labels
if LABELS.exists():
    labels_df = pd.read_csv(LABELS)
    label_districts = set(labels_df["district_clean"].str.upper().str.strip().unique())
    geo_districts   = set(centroids_df["district_name"].str.upper().str.strip().unique())
    matched = label_districts & geo_districts
    match_rate = len(matched)/len(label_districts)*100 if label_districts else 0
    print(f"\nDistrict match rate: {len(matched)}/{len(label_districts)} = {match_rate:.1f}%")
    if match_rate < 85:
        unmatched = label_districts - geo_districts
        print(f"WARN: {len(unmatched)} unmatched districts: {sorted(unmatched)[:20]}")
    else:
        print("Match rate OK (>85%)")
else:
    print("WARN: epiclim_labels.csv not found — skipping match check")

OUT.parent.mkdir(parents=True, exist_ok=True)
centroids_df.to_csv(OUT, index=False)
print(f"\nOutput: {len(centroids_df):,} rows -> {OUT}")
print("PASS: district_centroids_v2.csv written")
