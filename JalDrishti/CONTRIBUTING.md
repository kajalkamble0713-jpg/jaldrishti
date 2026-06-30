# Contributing to JalDrishti

Thank you for contributing. This document covers the development workflow, code standards, and how to submit changes.

---

## Team

| Name | Roll No. | Area |
|------|----------|------|
| Josna Fernandes | 4AL23CS056 | Dashboard, Risk Map, Trends |
| Kajal Kamble | 4AL23CS058 | Feature engineering, ML, SHAP |
| Hemalatha K B | 4AL23CS053 | AWS pipeline, District Analysis, NASA LST |
| Arpita Gavi | 4AL23CS023 | Economic calculator, mock data, outbreak data |

**Guide:** Dr. Chandra Naik, Associate Professor
**Institution:** Alva's Institute of Engineering & Technology, Moodbidri

---

## Getting Started

```bash
# 1. Clone the repository
git clone <repository-url>
cd JalDrishti

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate mock data and train models
python src/generate_mock_data.py
python src/feature_engineering.py
python src/model_trainer.py

# 5. Run the dashboard
streamlit run dashboard/app.py
```

---

## Project Structure

```
JalDrishti/
├── config/                     Disease fingerprint thresholds
├── dashboard/app.py            Main Streamlit dashboard
├── data/
│   ├── geo/                    GeoJSON + centroids
│   └── processed/              CSV data files
├── models/                     Trained .pkl model files
├── src/                        Pipeline and utility scripts
├── requirements.txt
├── Dockerfile
├── CHANGELOG.md
└── CONTRIBUTING.md
```

---

## Development Workflow

### Branching

- `main` — stable, production-ready
- `feature/<name>` — new features
- `fix/<name>` — bug fixes
- `docs/<name>` — documentation only

```bash
git checkout -b feature/my-feature
```

### Commit Messages

Use the format: `type: short description`

| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `style` | CSS/UI changes only |
| `refactor` | Code restructure, no behavior change |
| `docs` | Documentation only |
| `data` | Data pipeline changes |
| `model` | ML model changes |

Examples:
```
feat: add 30-day forecast to district analysis tab
fix: remove duplicate generate_30day_forecast definition
style: switch font to Outfit, accent to teal #0D9488
docs: add CONTRIBUTING.md and CHANGELOG.md
```

### Pull Requests

1. Branch from `main`
2. Make your changes
3. Run `python -m py_compile dashboard/app.py` — must pass
4. Test the dashboard: `streamlit run dashboard/app.py`
5. Open a PR with a clear description of what changed and why

---

## Code Standards

### Dashboard (`dashboard/app.py`)

- Every function must have a docstring
- New helper functions go in the `NEW HELPER FUNCTIONS` section
- Never delete existing functions — only add or extend
- All new Plotly charts must use the theme palette:
  ```python
  plot_bgcolor='#131920'
  paper_bgcolor='rgba(0,0,0,0)'
  font=dict(color='#5A7080', family='Outfit, sans-serif')
  gridcolor='#243040'
  ```
- All new inline HTML must use `font-family:"Outfit",sans-serif`

### Data Pipeline (`src/`)

- All scripts must be runnable standalone from the `JalDrishti/` directory
- Use relative paths from the project root
- Add resume capability for long-running pipelines (check existing output before processing)
- Log progress with `print()` — no external logging libraries

### Models

- Never overwrite trained models without explicit intent
- Document hyperparameters in comments
- Keep temporal split: Train 2019–2021, Val 2022, Test 2023

---

## Running Tests

There is no automated test suite yet. Manual validation:

```bash
# Validate data pipeline
python src/validate_pipeline.py

# Check dashboard syntax
python -m py_compile dashboard/app.py

# Run dashboard and verify all 5 tabs load
streamlit run dashboard/app.py
```

---

## Adding a New Tab

1. Add the tab name to the `st.tabs([...])` call
2. Add a `with tabN:` block following the existing pattern
3. Use the standard section header HTML:
   ```python
   st.markdown("""
   <div style='margin-bottom:1rem;'>
       <p style='font-family:"Outfit",sans-serif; font-size:1.0625rem; font-weight:700;
                 color:#F0F4F8; margin:0;'>Tab Title</p>
       <p style='font-family:"Outfit",sans-serif; color:#5A7080; font-size:0.78rem; margin:0.2rem 0 0;'>
           Subtitle description
       </p>
   </div>
   """, unsafe_allow_html=True)
   ```

---

## Deployment

### Local
```bash
streamlit run dashboard/app.py
```

### Docker
```bash
docker build -t jaldrishti .
docker run -p 8501:8501 jaldrishti
```

### Streamlit Community Cloud
1. Push to GitHub (public or private repo)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Set main file path: `dashboard/app.py`
5. Set working directory: `JalDrishti`
6. Deploy — live in ~3 minutes

---

## Questions

Reach out to the team or open an issue in the repository.
