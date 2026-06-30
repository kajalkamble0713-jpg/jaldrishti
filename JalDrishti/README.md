# JalDrishti — Waterborne Disease Early Warning System
**Satellite-Based Early Warning System for Waterborne Disease Outbreaks in India**

Final Year B.E. Computer Engineering Major Project
**Alva's Institute of Engineering & Technology, Moodbidri**
Guide: Dr. Chandra Naik | Department of CSE | 2025–2026

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Overview
JalDrishti Lite predicts district/state-level outbreak risk for ADD (Diarrhoea), Cholera,
and Typhoid **2–4 weeks in advance** using free satellite imagery and machine learning.

**This is NOT a real-time detection system** — it gives advance environmental risk warnings
based on satellite-observed water quality conditions that precede outbreaks.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/kajalkamble0713-jpg/jaldrishti.git
cd jaldrishti/JalDrishti

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the full pipeline (in order)
python src/process_epiclim.py
python src/process_nhp_typhoid.py
python src/prepare_geo.py
python src/build_svi.py
python src/build_feature_matrix.py
python src/train_models.py
python src/explain_models.py
python src/mock_data_generator.py   # optional safety net

# 5. Launch dashboard
streamlit run dashboard/app.py
```

Open browser at **http://localhost:8501**

---

## Data Sources

| Source | Dataset | URL | Limitations |
|--------|---------|-----|-------------|
| AWS Earth Search | Sentinel-2 L2A water quality | https://earth-search.aws.element84.com/v1 | Free, no login |
| NASA Earthdata | MODIS MOD11A1 V061 LST | https://earthdata.nasa.gov | Free account required |
| EpiClim / Zenodo | ADD + Cholera district outbreak labels | https://zenodo.org/records/14580510 | 2009–2022 only |
| NHP / CBHI India | Typhoid state-level case counts | https://cbhidghs.mohfw.gov.in | PDF reports, state-level only |
| DataMeet | India district GeoJSON | https://github.com/datameet/maps | 594 districts |
| Census 2011 / NFHS-5 | Social Vulnerability Index | Existing pipeline | Pre-2021 data |

---

## Model Performance Summary

| Disease | Level | Train Period | Test Period | ROC-AUC | PR-AUC |
|---------|-------|-------------|------------|---------|--------|
| ADD | District | 2020–2022 | 2023 | 0.667 | 0.101 |
| Cholera | District | 2020–2022 | 2023 | 0.654 | 0.078 |
| Typhoid | State | 2019–2022 | 2023 | 0.796 | 0.772 |

**Note:** ADD/Cholera ROC-AUC reflects the challenging district-level imbalanced task
(~4–6% outbreak prevalence). Typhoid performs better as state aggregation reduces noise.
Full 80-district JalDrishti pipeline achieves ROC-AUC 0.84/0.82/0.81 (see research paper).

---

## Documented Limitations

1. **Typhoid is state-level only** — no free district-level Typhoid dataset exists in India
2. **Reduced district scope (Lite)** — full 700+ district pipeline requires several hours of satellite fetching. Re-run with full dataset by extending `fetch_sentinel2.py` scope
3. **Satellite revisit delay** — ~5–6 days; monthly composites average this out
4. **SVI uses Census 2011** — post-2021 Swachh Bharat improvements not reflected
5. **EpiClim under-reporting** — rural ADD cases managed without formal care are missed

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| 📋 Overview | Project description, data sources, limitations disclaimer |
| 🗺️ Risk Map | Interactive India map — districts coloured by outbreak risk |
| 🔍 District Deep Dive | Time series, risk scores, SHAP feature explanations |
| 📊 Model Performance | Metrics table, SHAP charts, limitations & future work |

---

## Deployment (Streamlit Community Cloud)

```bash
# 1. Push to GitHub
git add .
git commit -m "Update"
git push -u origin main
```

Then:
1. Go to **https://share.streamlit.io**
2. Sign in with GitHub (`kajalkamble0713-jpg`)
3. Click **New app**
4. Fill in:
   - Repository: `kajalkamble0713-jpg/jaldrishti`
   - Branch: `main`
   - Main file path: `JalDrishti/dashboard/app.py`
5. Click **Deploy**

---

## Project Structure

```
jaldrishti/
├── data/
│   ├── raw/                    # EpiClim CSV, NHP PDFs
│   ├── processed/              # Feature matrices, labels, SVI
│   └── geo/                    # GeoJSON, centroids
├── models/                     # Trained .pkl models, SHAP outputs
├── src/                        # Pipeline scripts (run in order)
│   ├── process_epiclim.py      # Step 1.1 — ADD/Cholera labels
│   ├── process_nhp_typhoid.py  # Step 1.2 — Typhoid labels
│   ├── prepare_geo.py          # Step 2   — Centroids
│   ├── build_svi.py            # Step 4   — SVI scores
│   ├── build_feature_matrix.py # Step 5   — Final feature matrix
│   ├── train_models.py         # Step 6   — XGBoost training
│   ├── explain_models.py       # Step 7   — SHAP explainability
│   └── mock_data_generator.py  # Step 9   — Demo data fallback
├── dashboard/
│   └── app.py                  # Streamlit dashboard (4 pages)
├── config/
│   └── geojson_property_keys.json
└── requirements.txt
```

## Status
Environment setup and full pipeline: **COMPLETE** ✅
