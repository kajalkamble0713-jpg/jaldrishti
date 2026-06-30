"""
Step 6: Download NHP (National Health Profile) PDFs for Typhoid data.
"""
import requests
from pathlib import Path
import re

OUT_DIR = Path("data/raw/nhp_typhoid_raw")

KNOWN_URLS = {
    2019: "http://cbhidghs.mohfw.gov.in/sites/default/files/NHP/National-health-2019.pdf",
    2020: "http://cbhidghs.mohfw.gov.in/sites/default/files/2024-09/National_Health_Profile_2020.pdf",
    2022: "http://cbhidghs.mohfw.gov.in/sites/default/files/2024-09/national-health-profile-2022.pdf",
}

def try_find_year_url(year):
    """Try to find PDF URL for a given year from the NHP index page."""
    index_url = "https://cbhidghs.mohfw.gov.in/e-national-health-profile"
    try:
        r = requests.get(index_url, timeout=30)
        r.raise_for_status()
        links = re.findall(r'href=["\']([^"\']+\.pdf[^"\']*)["\']', r.text, re.IGNORECASE)
        year_links = [l for l in links if str(year) in l]
        if year_links:
            url = year_links[0]
            if not url.startswith("http"):
                url = "https://cbhidghs.mohfw.gov.in" + url
            return url
    except Exception as e:
        print(f"    Could not fetch index page: {e}")
    return None

def download_pdf(url, out_path, year):
    try:
        r = requests.get(url, timeout=120, stream=True, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        with open(out_path, "wb") as fh:
            for chunk in r.iter_content(chunk_size=65536):
                fh.write(chunk)
        size = out_path.stat().st_size
        # Verify PDF magic bytes
        with open(out_path, "rb") as fh:
            magic = fh.read(4)
        if magic != b"%PDF":
            print(f"    WARNING: File does not start with %PDF magic bytes")
            return False, size
        # Quick page count via pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(out_path) as pdf:
                pages = len(pdf.pages)
            print(f"    Pages: {pages}")
        except Exception as e:
            print(f"    Could not read page count: {e}")
            pages = "unknown"
        return True, size
    except Exception as e:
        print(f"    Download FAILED: {e}")
        return False, 0

def download_nhp():
    print("=== NHP PDF Download ===")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {}

    for year in [2019, 2020, 2021, 2022, 2023]:
        out_file = OUT_DIR / f"National_Health_Profile_{year}.pdf"
        print(f"\n  Year {year}:")

        url = KNOWN_URLS.get(year)
        if not url:
            print(f"    No known URL — trying to find from index page...")
            url = try_find_year_url(year)
            if not url:
                print(f"    Could not find URL for {year} — SKIPPED")
                results[year] = "SKIPPED — URL not found"
                continue
            print(f"    Found URL: {url}")

        print(f"    URL: {url}")
        ok, size = download_pdf(url, out_file, year)
        if ok:
            print(f"    File size: {size:,} bytes — STATUS: PASS")
            results[year] = f"PASS ({size:,} bytes)"
        else:
            results[year] = "FAIL"

    print("\n  Summary:")
    for year, status in results.items():
        print(f"    {year}: {status}")
    return results

if __name__ == "__main__":
    download_nhp()
