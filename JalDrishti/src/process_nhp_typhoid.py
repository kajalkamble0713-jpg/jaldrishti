"""
Phase 2 Step 1.2 — Process NHP PDFs for Typhoid state-level labels
Usage: python src/process_nhp_typhoid.py
Output: data/processed/nhp_typhoid_labels.csv
NOTE: Typhoid data is STATE-LEVEL only (NHP reports are state-wise summaries).
      This is a documented limitation — no free district-level Typhoid source exists.
"""
import pdfplumber, re, json, pandas as pd
from pathlib import Path

BASE    = Path(__file__).parent.parent
NHP_DIR = BASE / "data/raw/nhp_typhoid_raw"
OUT     = BASE / "data/processed/nhp_typhoid_labels.csv"

TYPHOID_KEYWORDS = ["typhoid","enteric fever","enteric"]
DISEASE_TABLE_KW = ["communicable","health status","state","disease"]

def normalize_state(s):
    s = str(s).strip().upper()
    s = re.sub(r"[^\w\s]","",s)
    s = re.sub(r"\s+"," ",s)
    return s.strip()

def find_typhoid_page(pdf):
    """Find the page(s) containing typhoid data."""
    hits = []
    for i, page in enumerate(pdf.pages):
        text = (page.extract_text() or "").lower()
        if any(kw in text for kw in TYPHOID_KEYWORDS):
            hits.append(i)
    return hits

def extract_table_from_page(page):
    """Try to extract a structured table from the page."""
    tables = page.extract_tables()
    if tables:
        return tables
    # Fallback: extract raw text lines
    text = page.extract_text() or ""
    return text

def parse_typhoid_from_tables(tables, year):
    """Parse (state, cases) from table data."""
    rows = []
    for table in tables:
        if not table:
            continue
        # Find typhoid column
        header_row = None
        typhoid_col = None
        for i, row in enumerate(table):
            row_lc = [str(c).lower() if c else "" for c in row]
            if any("typhoid" in c or "enteric" in c for c in row_lc):
                header_row = i
                typhoid_col = next((j for j,c in enumerate(row_lc)
                                    if "typhoid" in c or "enteric" in c), None)
                break
        if header_row is None or typhoid_col is None:
            continue
        # State column is usually first or second
        state_col = 0
        for data_row in table[header_row+1:]:
            if not data_row or len(data_row) <= typhoid_col:
                continue
            state  = str(data_row[state_col] or "").strip()
            cases  = str(data_row[typhoid_col] or "").strip()
            if not state or state.lower() in ["","total","india","grand total"]:
                continue
            # Clean cases: remove commas, spaces
            cases_clean = re.sub(r"[^\d]","", cases)
            if cases_clean:
                rows.append({"state_clean": normalize_state(state),
                             "year": year,
                             "typhoid_cases": int(cases_clean)})
    return rows

print("=== process_nhp_typhoid.py ===")
pdfs = sorted(NHP_DIR.glob("*.pdf")) if NHP_DIR.exists() else []
print(f"Found {len(pdfs)} PDFs in {NHP_DIR}")

if not pdfs:
    print("WARN: No NHP PDFs found. Using outbreak_labels.csv typhoid column as fallback.")
    # Use the existing processed outbreak_labels which already has typhoid data
    existing = BASE / "data/processed/outbreak_labels.csv"
    if existing.exists():
        df = pd.read_csv(existing)
        if "typhoid_outbreak" in df.columns:
            # Aggregate to state level
            state_typhoid = df.groupby(["state_name","year","month"])["typhoid_outbreak"].max().reset_index()
            state_typhoid.columns = ["state_clean","year","month","outbreak_typhoid"]
            state_typhoid["state_clean"] = state_typhoid["state_clean"].apply(normalize_state)
            OUT.parent.mkdir(parents=True, exist_ok=True)
            state_typhoid.to_csv(OUT, index=False)
            print(f"Fallback: derived state-level typhoid from outbreak_labels.csv")
            print(f"Output: {len(state_typhoid):,} rows -> {OUT}")
            print(f"States: {state_typhoid.state_clean.nunique()}, Outbreaks: {state_typhoid.outbreak_typhoid.sum()}")
            print("PASS (fallback mode — NHP PDFs not available)")
            raise SystemExit(0)
    print("FAIL: No NHP PDFs and no fallback data available.")
    raise SystemExit(1)

all_rows = []
for pdf_path in pdfs:
    # Extract year from filename
    m = re.search(r"(20\d{2})", pdf_path.name)
    if not m:
        print(f"  SKIP {pdf_path.name}: cannot determine year from filename")
        continue
    year = int(m.group(1))
    print(f"\n  Processing {pdf_path.name} (year={year})...")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"  Pages: {total_pages}")
            typhoid_pages = find_typhoid_page(pdf)
            print(f"  Typhoid keyword found on pages: {[p+1 for p in typhoid_pages]}")
            if not typhoid_pages:
                print(f"  WARN: No typhoid keyword found in {pdf_path.name}")
                continue
            year_rows = []
            for pg_idx in typhoid_pages[:5]:  # check first 5 hits
                page = pdf.pages[pg_idx]
                tables = page.extract_tables()
                print(f"    Page {pg_idx+1}: {len(tables)} tables found")
                if tables:
                    # Show sample
                    for t in tables[:1]:
                        print(f"    Sample table (first 3 rows): {t[:3]}")
                    parsed = parse_typhoid_from_tables(tables, year)
                    year_rows.extend(parsed)
            print(f"  Parsed {len(year_rows)} state-rows for {year}")
            all_rows.extend(year_rows)
    except Exception as e:
        print(f"  ERROR in {pdf_path.name}: {e}")

if all_rows:
    df = pd.DataFrame(all_rows)
    # Compute binary outbreak flag: above median cases for that state
    df["median_cases"] = df.groupby("state_clean")["typhoid_cases"].transform("median")
    df["outbreak_typhoid"] = (df["typhoid_cases"] > df["median_cases"]).astype(int)
    df = df.drop(columns=["median_cases"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nOutput: {len(df):,} rows -> {OUT}")
    print(f"States: {df.state_clean.nunique()}, Outbreak flag: {df.outbreak_typhoid.sum()} positive")
    print("PASS: nhp_typhoid_labels.csv written")
else:
    print("\nWARN: Could not extract any typhoid data from PDFs.")
    print("Using fallback: deriving state-level typhoid from existing outbreak_labels.csv...")
    existing = BASE / "data/processed/outbreak_labels.csv"
    if existing.exists():
        df = pd.read_csv(existing)
        state_typhoid = df.groupby(["state_name","year","month"])["typhoid_outbreak"].max().reset_index()
        state_typhoid.columns = ["state_clean","year","month","outbreak_typhoid"]
        state_typhoid["state_clean"] = state_typhoid["state_clean"].apply(normalize_state)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        state_typhoid.to_csv(OUT, index=False)
        print(f"Fallback output: {len(state_typhoid):,} rows -> {OUT}")
        print("PASS (fallback from outbreak_labels.csv)")
    else:
        print("FAIL: No data produced.")
