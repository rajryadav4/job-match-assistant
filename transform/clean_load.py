import glob
import json
import re

import pandas as pd
from bs4 import BeautifulSoup
from psycopg2.extras import execute_values

from db import get_connection

RAW_DIR = "data/raw"


# ---------- EXTRACT ----------
def load_raw_files():
    """Read every raw JSON file and combine the job records."""
    records = []
    for path in glob.glob(f"{RAW_DIR}/*.json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        records.extend(data.get("results", []))
    print(f"Loaded {len(records)} raw records")
    return records


# ---------- TRANSFORM ----------
def clean_text(value):
    """Remove HTML tags and collapse extra whitespace."""
    if not value:
        return None
    text = BeautifulSoup(value, "html.parser").get_text(" ")
    return re.sub(r"\s+", " ", text).strip()


def flatten(records):
    """Pull nested API fields into flat columns."""
    rows = []
    for r in records:
        rows.append({
            "source": "adzuna",
            "external_id": str(r.get("id")),
            "title": clean_text(r.get("title")),
            "company": (r.get("company") or {}).get("display_name"),
            "location": (r.get("location") or {}).get("display_name"),
            "salary_min": r.get("salary_min"),
            "salary_max": r.get("salary_max"),
            "description": clean_text(r.get("description")),
            "url": r.get("redirect_url"),
            "date_posted": r.get("created"),
        })
    return pd.DataFrame(rows)


def clean(df):
    before = len(df)
    df = df.dropna(subset=["title", "external_id"]).copy()
    df["date_posted"] = pd.to_datetime(df["date_posted"], errors="coerce")

    for col in ["company", "location"]:
        df[col] = df[col].astype("string").str.strip()

    # Force salaries to numbers first (avoids errors when a column is all empty)
    for col in ["salary_min", "salary_max"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] < 1000, col] = None

    df = df.drop_duplicates(subset=["source", "external_id"])
    df = df.drop_duplicates(subset=["title", "company", "location"])

    # Postgres needs None instead of pandas NaN/NaT/NA
    df = df.astype(object).where(pd.notnull(df), None)

    print(f"Cleaned: {before} -> {len(df)} rows")
    return df


# ---------- LOAD ----------
def load(df):
    if df.empty:
        print("Nothing to load")
        return
    cols = list(df.columns)
    values = [tuple(row) for row in df.itertuples(index=False)]

    sql = f"""
        INSERT INTO jobs ({", ".join(cols)})
        VALUES %s
        ON CONFLICT (source, external_id) DO UPDATE SET
            title       = EXCLUDED.title,
            description = EXCLUDED.description,
            salary_min  = EXCLUDED.salary_min,
            salary_max  = EXCLUDED.salary_max,
            fetched_at  = NOW();
    """

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, values)
        print(f"Loaded {len(values)} rows into the jobs table")
    finally:
        conn.close()


if __name__ == "__main__":
    raw = load_raw_files()
    if raw:
        load(clean(flatten(raw)))
