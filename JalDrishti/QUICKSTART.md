# Quick Start — JalDrishti

## Run the Dashboard

```bash
cd JalDrishti
streamlit run dashboard/app.py
```

Open **http://localhost:8501**

---

## First Time Setup (5 minutes)

```bash
pip install -r requirements.txt
python src/generate_mock_data.py
python src/feature_engineering.py
python src/model_trainer.py
streamlit run dashboard/app.py
```

---

## Dashboard Tabs

| Tab | Description |
|-----|-------------|
| Risk Map | India-wide district risk choropleth + top 10 table |
| District Analysis | Satellite index radar, index cards, monthly trend |
| SHAP Explainer | Feature importance + pathogen fingerprint match |
| Economic Impact | Cost projections, ROI calculator, 12-month forecast |
| Trends | Annual frequency, seasonal patterns, state heatmap |

---

## Sidebar Controls

- **State / District** — Filter to any district across India
- **Time Period** — Slide through 2019–2023 monthly data
- **Diseases** — Toggle ADD, Cholera, Typhoid monitoring

---

## Risk Levels

| Score | Level | Action |
|-------|-------|--------|
| 0–40% | Low | Routine monitoring |
| 40–70% | Medium | Increased vigilance |
| 70–85% | High | Prepare interventions |
| 85–100% | Critical | Immediate action |

---

## Risk Formula

```
Final Risk = (70% × Satellite Risk) + (30% × Social Vulnerability Index)
```

---

## Regenerate Data

```bash
python src/generate_mock_data.py    # Recreate mock satellite + SVI + outbreak data
python src/feature_engineering.py  # Build 32-feature ML matrix
python src/model_trainer.py        # Retrain XGBoost models
```

---

## Production Pipeline (Real Satellite Data)

```bash
python src/download_outbreak_data.py   # ~10 min
python src/build_district_filter.py    # ~3 min
python src/aws_pipeline.py             # ~20–30 hrs (resumable)
python src/nasa_lst_pipeline.py        # ~10–15 hrs (resumable)
python src/run_real_data_pipeline.py   # ~1 hr
streamlit run dashboard/app.py
```

---

## Troubleshooting

**Port in use**
```bash
# Windows
taskkill /F /IM streamlit.exe
streamlit run dashboard/app.py
```

**Data files missing**
```bash
python src/generate_mock_data.py
```

**Map shows grey / no choropleth**
Place `india_districts.geojson` in `data/geo/`. Download from [datameet/maps](https://github.com/datameet/maps).

---

## Team

Josna Fernandes · Kajal Kamble · Hemalatha K B · Arpita Gavi
Guide: Dr. Chandra Naik | Alva's Institute of Engineering & Technology | 2025–2026
