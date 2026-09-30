# Job Match Assistant

ETL pipeline that collects real job postings from the Adzuna API, cleans and stores
them in PostgreSQL, tracks in-demand skills, and visualizes the job market in a
Streamlit dashboard. Phase 2 will match jobs against a resume using embeddings and a local LLM.

## Quick start
```bash
python3 -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                              # then add your Adzuna ID and key
docker run --name jobs-db -e POSTGRES_PASSWORD=change_me -e POSTGRES_DB=jobs \
  -p 5432:5432 -v jobs-data:/var/lib/postgresql/data -d pgvector/pgvector:pg16
docker exec -i jobs-db psql -U postgres -d jobs < schema.sql
python run_pipeline.py
streamlit run app/dashboard.py                    # opens http://localhost:8501
```

## Architecture
Adzuna API -> raw JSON (data/raw) -> clean & dedupe (pandas) -> PostgreSQL
-> regex skill extraction (34 skills) -> Streamlit dashboard.
GitHub Actions workflow included for daily scheduled runs (requires a cloud database).

## Features
- API ingestion with pagination and exponential-backoff retries
- HTML cleanup, salary validation, and duplicate removal
- Normalized schema (jobs, skills, job_skills) with idempotent upserts
- Dashboard: top skills, locations, companies, posting trends, salary by skill

## First run results
750 postings fetched -> 711 unique jobs. Top skills: Machine Learning, AWS, LLMs, Python, SQL.

## Tech stack
Python, pandas, BeautifulSoup, PostgreSQL + pgvector, Docker, Streamlit, GitHub Actions

## Future improvements
- Process only new raw files instead of re-reading all of them
- Cross-batch duplicate detection for reposted jobs
- Add Remotive API for full job descriptions and better skill detection
- Phase 2: sentence-transformers embeddings + pgvector matching + Ollama resume tailoring
- Phase 3: public deployment (Streamlit Community Cloud, OpenTofu)
