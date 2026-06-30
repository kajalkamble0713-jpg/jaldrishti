# ── JalDrishti — Dockerfile ──────────────────────────────────────────────────
# One-command deployment:
#   docker build -t jaldrishti .
#   docker run -p 8501:8501 jaldrishti
#
# Then open http://localhost:8501
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# System dependencies for geopandas / rasterio
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgdal-dev \
        gdal-bin \
        libproj-dev \
        proj-data \
        proj-bin \
        libgeos-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the full project
COPY . .

# Streamlit config — disable telemetry, set port
RUN mkdir -p /root/.streamlit
RUN echo '\
[general]\n\
email = ""\n\
\n\
[server]\n\
headless = true\n\
port = 8501\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
' > /root/.streamlit/config.toml

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the dashboard from the JalDrishti/ subdirectory
WORKDIR /app/JalDrishti

# Generate mock data if processed files don't exist, then launch
CMD ["sh", "-c", "\
    if [ ! -f data/processed/master_satellite_indices.csv ]; then \
        echo 'Generating mock data...' && \
        python src/generate_mock_data.py && \
        python src/feature_engineering.py && \
        python src/model_trainer.py; \
    fi && \
    streamlit run dashboard/app.py \
"]
