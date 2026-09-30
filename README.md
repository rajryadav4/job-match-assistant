# Job Match Assistant

Automated pipeline that collects job postings daily, tracks in-demand skills,
and (Phase 2) matches them against a resume using embeddings and an LLM.

## Quick start
```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                              # then fill in real values
docker run --name jobs-db -e POSTGRES_PASSWORD=change_me -e POSTGRES_DB=jobs \
  -p 5432:5432 -v jobs-data:/var/lib/postgresql/data -d pgvector/pgvector:pg16
docker exec -i jobs-db psql -U postgres -d jobs < schema.sql
python run_pipeline.py
streamlit run app/dashboard.py
```

## Architecture
Adzuna API -> raw JSON (data/raw) -> clean & dedupe (pandas) -> PostgreSQL
-> regex skill extraction -> Streamlit dashboard. Scheduled daily with GitHub Actions.

## Tech stack
Python, pandas, PostgreSQL + pgvector, Docker, Streamlit, GitHub Actions

## Future improvements
- Process only new raw files instead of re-reading all of them
- Cross-batch duplicate detection for reposted jobs
- Phase 2: embeddings + LLM resume tailoring
- Phase 3: AWS deployment with Terraform
