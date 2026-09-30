import json
import os
import time
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------- CONFIGURATION ----------
APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")
COUNTRY = os.getenv("ADZUNA_COUNTRY", "us")

SEARCH_TERMS = [
    "data engineer",
    "data analyst",
    "cloud engineer",
    "machine learning engineer",
    "ai engineer",
]
PAGES_PER_TERM = 3
RESULTS_PER_PAGE = 50
MAX_DAYS_OLD = 7
PAUSE_SECONDS = 1

RAW_DIR = Path("data/raw")
BASE_URL = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search"


def fetch_page(term, page, retries=3):
    """Fetch one page of results. Retries on temporary errors."""
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "what": term,
        "results_per_page": RESULTS_PER_PAGE,
        "max_days_old": MAX_DAYS_OLD,
        "content-type": "application/json",
    }
    url = f"{BASE_URL}/{page}"

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429 or resp.status_code >= 500:
                wait = 2 ** attempt
                print(f"  Got {resp.status_code}, retrying in {wait}s...")
                time.sleep(wait)
                continue
            print(f"  Error {resp.status_code}: {resp.text[:200]}")
            return None
        except requests.RequestException as e:
            wait = 2 ** attempt
            print(f"  Network error ({e}), retrying in {wait}s...")
            time.sleep(wait)

    print(f"  Gave up on '{term}' page {page} after {retries} attempts")
    return None


def main():
    if not APP_ID or not APP_KEY:
        raise SystemExit("Missing ADZUNA_APP_ID or ADZUNA_APP_KEY in .env")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    all_results = []
    request_count = 0

    for term in SEARCH_TERMS:
        print(f"Searching: '{term}'")
        for page in range(1, PAGES_PER_TERM + 1):
            data = fetch_page(term, page)
            request_count += 1
            if not data:
                break
            results = data.get("results", [])
            for job in results:
                job["search_term"] = term
            all_results.extend(results)
            print(f"  Page {page}: {len(results)} jobs")
            if len(results) < RESULTS_PER_PAGE:
                break
            time.sleep(PAUSE_SECONDS)

    today = date.today().isoformat()
    out_path = RAW_DIR / f"adzuna_{today}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {"fetched_on": today, "request_count": request_count,
             "results": all_results},
            f, indent=2, ensure_ascii=False,
        )

    print(f"\nDone: {len(all_results)} jobs from {request_count} requests")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
