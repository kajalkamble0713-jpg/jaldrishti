"""
Step 3: Verify all required package imports work correctly.
"""
import sys

packages = [
    ("pystac_client", "pystac_client"),
    ("odc.stac", "odc.stac"),
    ("rioxarray", "rioxarray"),
    ("dask", "dask"),
    ("earthaccess", "earthaccess"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("geopandas", "geopandas"),
    ("shapely", "shapely"),
    ("fiona", "fiona"),
    ("pyproj", "pyproj"),
    ("openpyxl", "openpyxl"),
    ("xlrd", "xlrd"),
    ("xgboost", "xgboost"),
    ("sklearn", "scikit-learn"),
    ("imblearn", "imbalanced-learn"),
    ("shap", "shap"),
    ("scipy", "scipy"),
    ("streamlit", "streamlit"),
    ("folium", "folium"),
    ("streamlit_folium", "streamlit-folium"),
    ("plotly", "plotly"),
    ("pdfplumber", "pdfplumber"),
    ("camelot", "camelot-py"),
    ("requests", "requests"),
    ("tqdm", "tqdm"),
    ("joblib", "joblib"),
]

passed = []
failed = []

for module, pkg_name in packages:
    try:
        __import__(module)
        passed.append(pkg_name)
    except ImportError as e:
        failed.append((pkg_name, str(e)))

print(f"\n{'='*50}")
print(f"IMPORT VERIFICATION RESULTS")
print(f"{'='*50}")
print(f"PASSED ({len(passed)}/{len(packages)}):")
for p in passed:
    print(f"  ✓ {p}")
if failed:
    print(f"\nFAILED ({len(failed)}):")
    for pkg, err in failed:
        print(f"  ✗ {pkg}: {err}")
else:
    print("\nALL IMPORTS OK")
