from ingestion.fetch_jobs import main as fetch_jobs
from transform.clean_load import load_raw_files, flatten, clean, load
from transform.extract_skills import main as extract_skills

if __name__ == "__main__":
    print("=== STEP 1: FETCH ===")
    fetch_jobs()

    print("\n=== STEP 2-3: CLEAN AND LOAD ===")
    raw = load_raw_files()
    if raw:
        load(clean(flatten(raw)))

    print("\n=== STEP 4: EXTRACT SKILLS ===")
    extract_skills()

    print("\nPipeline complete.")
