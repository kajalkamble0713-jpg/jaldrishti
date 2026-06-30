"""
JalDrishti Lite — Complete Setup Script (Steps 4-10)
Run from inside jaldrishti/ folder: python src/setup_complete.py
"""
import sys, os, json, requests, re, subprocess, platform
from pathlib import Path

RAW, GEO = Path("data/raw"), Path("data/geo")
NHP_DIR, CFG_DIR = Path("data/raw/nhp_typhoid_raw"), Path("config")
for d in [RAW, GEO, NHP_DIR, CFG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"
results = {}

# ── Step 3: Import check ──────────────────────────────────────────────────
print("\n[STEP 3] Import Verification")
pkg_map = [
    ("pystac_client","pystac-client"),("odc.stac","odc-stac"),
    ("rioxarray","rioxarray"),("dask","dask"),("earthaccess","earthaccess"),
    ("pandas","pandas"),("numpy","numpy"),("geopandas","geopandas"),
    ("shapely","shapely"),("fiona","fiona"),("pyproj","pyproj"),
    ("openpyxl","openpyxl"),("xlrd","xlrd"),("xgboost","xgboost"),
    ("sklearn","scikit-learn"),("imblearn","imbalanced-learn"),
    ("shap","shap"),("scipy","scipy"),("streamlit","streamlit"),
    ("folium","folium"),("streamlit_folium","streamlit-folium"),
    ("plotly","plotly"),("pdfplumber","pdfplumber"),
    ("camelot","camelot-py"),("requests","requests"),
    ("tqdm","tqdm"),("joblib","joblib"),
]
import_pass, import_fail = [], []
for mod, pkg in pkg_map:
    try:
        __import__(mod)
        import_pass.append(pkg)
        print(f"  OK  {pkg}")
    except ImportError as e:
        import_fail.append((pkg, str(e)))
        print(f"  XX  {pkg}: {e}")
results["imports"] = {"passed": len(import_pass), "failed": import_fail,
                      "status": PASS if not import_fail else FAIL}

# ── Step 4: EpiClim ───────────────────────────────────────────────────────
print("\n[STEP 4] EpiClim Dataset (Zenodo)")
import pandas as pd
EPICLIM = RAW / "epiclim_raw.csv"
try:
    api_r = requests.get("https://zenodo.org/api/records/14580510", timeout=30)
    api_r.raise_for_status()
    files = api_r.json().get("files", [])
    csv_url = next((f["links"]["self"] for f in files if f.get("key","").endswith(".csv")), None)
    if not csv_url:
        raise ValueError("No CSV in Zenodo record")
    print(f"  Downloading from Zenodo...")
    dl = requests.get(csv_url, timeout=180, stream=True)
    dl.raise_for_status()
    with open(EPICLIM, "wb") as fh:
        for chunk in dl.iter_content(8192): fh.write(chunk)
    df = pd.read_csv(EPICLIM)
    nrows, size = len(df), EPICLIM.stat().st_size
    row_ok = "OK" if abs(nrows - 8985) < 2000 else f"WARNING expected ~8985"
    print(f"  Rows: {nrows} ({row_ok}), Cols: {list(df.columns)[:5]}")
    print(f"  File size: {size:,} bytes  STATUS: {PASS}")
    results["epiclim"] = {"status": PASS, "rows": nrows, "size": size}
except Exception as e:
    print(f"  ERROR: {e}  STATUS: {FAIL}")
    results["epiclim"] = {"status": FAIL, "error": str(e)}

# ── Step 5: GeoJSON ───────────────────────────────────────────────────────
print("\n[STEP 5] India District GeoJSON")
GEO_PATH = GEO / "india_districts.geojson"
PRIMARY  = "https://raw.githubusercontent.com/geohacker/india/master/district/india_district.geojson"
FALLBACK = "https://raw.githubusercontent.com/datameet/maps/master/Country/india-composite.geojson"
geo_ok = False
for label, url in [("PRIMARY", PRIMARY), ("FALLBACK", FALLBACK)]:
    try:
        print(f"  Trying {label}...")
        r = requests.get(url, timeout=180, stream=True)
        r.raise_for_status()
        with open(GEO_PATH, "wb") as fh:
            for chunk in r.iter_content(65536): fh.write(chunk)
        with open(GEO_PATH) as fh:
            geo = json.load(fh)
        feats = geo.get("features", [])
        props = feats[0]["properties"] if feats else {}
        all_keys = list(props.keys())
        name_k  = next((k for k in all_keys if any(x in k.lower() for x in ["name","dist"])), all_keys[0] if all_keys else None)
        state_k = next((k for k in all_keys if any(x in k.lower() for x in ["state","st_"])), None)
        code_k  = next((k for k in all_keys if any(x in k.lower() for x in ["code","dt_"])), None)
        key_cfg = {"district_name_key": name_k, "state_name_key": state_k,
                   "district_code_key": code_k, "all_property_keys": all_keys}
        with open(CFG_DIR / "geojson_property_keys.json","w") as fh:
            json.dump(key_cfg, fh, indent=2)
        size = GEO_PATH.stat().st_size
        print(f"  Features: {len(feats)}, Size: {size:,} bytes")
        print(f"  district_name_key='{name_k}', state_name_key='{state_k}', code_key='{code_k}'")
        print(f"  STATUS: {PASS}")
        results["geojson"] = {"status": PASS, "features": len(feats), "size": size, "keys": key_cfg}
        geo_ok = True; break
    except Exception as e:
        print(f"  {label} failed: {e}")
if not geo_ok:
    results["geojson"] = {"status": FAIL}

# ── Step 6: NHP PDFs ──────────────────────────────────────────────────────
print("\n[STEP 6] NHP PDFs")
KNOWN_URLS = {
    2019: "http://cbhidghs.mohfw.gov.in/sites/default/files/NHP/National-health-2019.pdf",
    2020: "http://cbhidghs.mohfw.gov.in/sites/default/files/2024-09/National_Health_Profile_2020.pdf",
    2022: "http://cbhidghs.mohfw.gov.in/sites/default/files/2024-09/national-health-profile-2022.pdf",
}

def find_nhp_url(year):
    try:
        r = requests.get("https://cbhidghs.mohfw.gov.in/e-national-health-profile", timeout=20)
        for l in re.findall(r'href=["\']([^"\']+\.pdf[^"\']*)["\']', r.text, re.I):
            if str(year) in l:
                return ("https://cbhidghs.mohfw.gov.in" + l) if not l.startswith("http") else l
    except: pass
    return None

nhp_res = {}
for yr in [2019, 2020, 2021, 2022, 2023]:
    url = KNOWN_URLS.get(yr) or find_nhp_url(yr)
    if not url:
        print(f"  {yr}: no URL — SKIPPED"); nhp_res[yr] = SKIP; continue
    out = NHP_DIR / f"National_Health_Profile_{yr}.pdf"
    try:
        r = requests.get(url, timeout=120, stream=True, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        with open(out,"wb") as fh:
            for c in r.iter_content(65536): fh.write(c)
        size = out.stat().st_size
        magic = open(out,"rb").read(4)
        pages = "?"
        try:
            import pdfplumber
            with pdfplumber.open(out) as pdf: pages = len(pdf.pages)
        except: pass
        st = PASS if magic == b"%PDF" else FAIL
        print(f"  {yr}: {size:,} bytes, {pages} pages — {st}")
        nhp_res[yr] = f"{st} ({size:,} bytes, {pages} pages)"
    except Exception as e:
        print(f"  {yr}: {e} — {FAIL}"); nhp_res[yr] = FAIL
results["nhp"] = nhp_res

# ── Step 7: AWS Earth Search ──────────────────────────────────────────────
print("\n[STEP 7] AWS Earth Search Connectivity")
try:
    from pystac_client import Client
    cat = Client.open("https://earth-search.aws.element84.com/v1")
    cols = [c.id for c in cat.get_collections()]
    has_s2 = "sentinel-2-l2a" in cols
    print(f"  Connected. {len(cols)} collections. sentinel-2-l2a={has_s2}")
    print(f"  STATUS: {PASS if has_s2 else FAIL}")
    results["aws"] = {"status": PASS if has_s2 else FAIL, "collections": len(cols), "s2_l2a": has_s2}
except Exception as e:
    print(f"  ERROR: {e}  STATUS: {FAIL}")
    results["aws"] = {"status": FAIL, "error": str(e)}

# ── Step 9: Git init ──────────────────────────────────────────────────────
print("\n[STEP 9] Git Init")
try:
    subprocess.run(["git","init"], check=True, capture_output=True, cwd=".")
    subprocess.run(["git","add",".gitignore","README.md","requirements.txt"],
                   capture_output=True, cwd=".")
    print(f"  Git initialised, base files staged.  STATUS: {PASS}")
    results["git"] = {"status": PASS}
except Exception as e:
    print(f"  {e}  STATUS: {FAIL}")
    results["git"] = {"status": FAIL}

# ── Final Report ──────────────────────────────────────────────────────────
print("\n" + "="*60)
print("FINAL SETUP REPORT")
print("="*60)
print(f"Python   : {sys.version.split()[0]} on {platform.system()}")
print(f"Venv     : {sys.executable}")
print()
imp = results["imports"]
print(f"[Packages]  {imp['status']}  {imp['passed']}/{imp['passed']+len(imp['failed'])} imports OK")
for pkg, err in imp["failed"]: print(f"  FAIL {pkg}: {err}")
print()
print(f"[EpiClim]   {results['epiclim']['status']}  rows={results['epiclim'].get('rows','?')}  size={results['epiclim'].get('size',0):,} bytes")
print(f"[GeoJSON]   {results['geojson']['status']}  features={results['geojson'].get('features','?')}  size={results['geojson'].get('size',0):,} bytes")
print(f"[NHP PDFs]")
for yr,st in results["nhp"].items(): print(f"  {yr}: {st}")
print(f"[AWS]       {results['aws']['status']}  sentinel-2-l2a={results['aws'].get('s2_l2a','?')}")
print(f"[Git]       {results['git']['status']}")
print()
print("CREDENTIALS STILL NEEDED FROM YOU:")
print("  1. NASA Earthdata (free) — https://urs.earthdata.nasa.gov")
print("     Needed for MODIS LST in the satellite pipeline phase.")
print("  2. GitHub account + empty repo 'jaldrishti' (free) — https://github.com")
print("     Provide repo URL so we can push code.")
print("  3. Streamlit Community Cloud (free, deployment only) — https://share.streamlit.io")
print("     Sign in with GitHub — no extra signup needed.")
print("="*60)
