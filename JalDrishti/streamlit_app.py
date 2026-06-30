# ── Streamlit Community Cloud entry point ────────────────────────────────────
# Streamlit Cloud runs from the repo root, so this file changes the working
# directory to JalDrishti/ and then executes the real dashboard.
#
# Deploy steps:
#   1. Push this repo to GitHub
#   2. Go to https://share.streamlit.io
#   3. Main file path: streamlit_app.py  (or JalDrishti/streamlit_app.py)
#   4. Click Deploy
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys

# Change working directory so all relative paths in app.py resolve correctly
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Execute the real dashboard
exec(open("dashboard/app.py").read())
