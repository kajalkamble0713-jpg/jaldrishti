# Changelog

All notable changes to JalDrishti are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [5.0.0] — April 2026

### Added
- Full 594-district coverage across 35 Indian states (up from 10 districts)
- Google Maps tile layer for the Risk Map tab
- Critical Alerts panel in sidebar showing top 5 high-risk districts live
- Stats bar in header (districts, states, data range, model AUC)
- Alert simulation system — Email/SMS alerts with session-state log
- Real XGBoost model predictions wired into District Analysis tab
- 30-day forward risk forecast with Wilson confidence intervals
- Data freshness indicator in sidebar showing file modification timestamps
- CSV export buttons on trend charts and alert log
- District HTML report generator
- GeoJSON + centroids cached at startup (`load_geo_data()`) — no re-reads on render
- Loading spinner on first data load
- Mobile-responsive CSS (metric cards, tabs, charts)
- `CHANGELOG.md`, `CONTRIBUTING.md`, `Dockerfile`, `.dockerignore`

### Changed
- Regenerated mock data for all 594 GeoJSON districts (35,640 rows)
- Retrained feature matrix on full district set (28,512 rows, 40 features)
- Dashboard font changed to Outfit; color scheme changed to teal (#0D9488)
- Tab headers redesigned with title + subtitle layout
- Risk Map stats panel replaced with color-coded bordered cards
- Sidebar logo updated; AUC badges use per-disease accent colors

### Fixed
- MemoryError on Folium map — replaced with cached GeoJSON + scatter markers
- IndentationError from duplicate CSS blocks left in Python scope
- `normalize_district_name` duplicate definition removed
- `export_chart_csv` NameError — moved definition before first call site

---

## [4.0.0] — March 2026

### Added
- SHAP Explainer tab with feature importance bar chart
- Economic Impact tab with ₹-denominated cost-benefit calculator
- 12-month economic burden projection with seasonal adjustment
- Pathogen fingerprint library table

### Changed
- Dashboard migrated from single-page to 5-tab layout
- Sidebar redesigned with state → district drill-down filter

---

## [3.0.0] — February 2026

### Added
- NASA MODIS LST pipeline (`src/nasa_lst_pipeline.py`) — resumable
- Land Surface Temperature integrated into satellite indices
- Social Vulnerability Index (SVI) merged into risk formula
- Risk formula: Final Risk = 0.70 × Satellite + 0.30 × SVI

---

## [2.0.0] — January 2026

### Added
- AWS Earth Search pipeline (`src/aws_pipeline.py`) — resumable, 42K district-months
- Sentinel-2 L2A water quality indices: Turbidity, NDCI, CDOM, NDWI, AWEI
- XGBoost classifiers for ADD, Cholera, Typhoid with SMOTE + GridSearchCV
- SHAP explainers saved as `.pkl` files
- Feature engineering: 32 features (lags, rolling means, YoY deltas, monsoon flag)

---

## [1.0.0] — December 2025

### Added
- Initial project scaffold
- Mock data generator (`src/generate_mock_data.py`)
- Basic Streamlit dashboard with risk map and district selector
- Pathogen fingerprint configuration (`config/pathogen_fingerprints.json`)
- EpiClim + IDSP outbreak data downloader
