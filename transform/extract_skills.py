"""Step 4: find skills mentioned in each job and store them in job_skills."""
import re

from psycopg2.extras import execute_values

from db import get_connection

# Skill name -> regex pattern. \b means "word boundary" so "sql" won't match inside "nosql".
# Add or remove skills here to change what gets tracked.
SKILLS = {
    "Python": r"\bpython\b",
    "SQL": r"\bsql\b",
    "Java": r"\bjava\b(?!\s*script)",
    "Scala": r"\bscala\b",
    "JavaScript": r"\bjavascript\b",
    "AWS": r"\baws\b|amazon web services",
    "Azure": r"\bazure\b",
    "GCP": r"\bgcp\b|google cloud",
    "Spark": r"\b(py)?spark\b",
    "Kafka": r"\bkafka\b",
    "Airflow": r"\bairflow\b",
    "dbt": r"\bdbt\b",
    "Snowflake": r"\bsnowflake\b",
    "Databricks": r"\bdatabricks\b",
    "PostgreSQL": r"\bpostgres(ql)?\b",
    "MongoDB": r"\bmongo(db)?\b",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes\b|\bk8s\b",
    "Terraform": r"\bterraform\b",
    "CI/CD": r"\bci/cd\b|continuous integration",
    "Git": r"\bgit\b",
    "Linux": r"\blinux\b",
    "ETL": r"\betl\b|\belt\b",
    "Tableau": r"\btableau\b",
    "Power BI": r"\bpower\s?bi\b",
    "Excel": r"\bexcel\b",
    "Pandas": r"\bpandas\b",
    "scikit-learn": r"scikit-learn|\bsklearn\b",
    "TensorFlow": r"\btensorflow\b",
    "PyTorch": r"\bpytorch\b",
    "Machine Learning": r"machine learning",
    "Deep Learning": r"deep learning",
    "NLP": r"\bnlp\b|natural language processing",
    "LLM": r"\bllms?\b|large language models?|generative ai|genai",
}
COMPILED = {name: re.compile(p, re.IGNORECASE) for name, p in SKILLS.items()}


def find_skills(text):
    if not text:
        return set()
    return {name for name, pattern in COMPILED.items() if pattern.search(text)}


def main():
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # 1. Make sure every skill exists in the skills table
                execute_values(
                    cur,
                    "INSERT INTO skills (name) VALUES %s ON CONFLICT (name) DO NOTHING",
                    [(s,) for s in SKILLS],
                )
                cur.execute("SELECT id, name FROM skills")
                skill_ids = {name: sid for sid, name in cur.fetchall()}

                # 2. Scan every job's title + description
                cur.execute("SELECT id, title, description FROM jobs")
                pairs = []
                for job_id, title, desc in cur.fetchall():
                    for skill in find_skills(f"{title or ''} {desc or ''}"):
                        pairs.append((job_id, skill_ids[skill]))

                # 3. Store links (ON CONFLICT keeps it idempotent)
                if pairs:
                    execute_values(
                        cur,
                        "INSERT INTO job_skills (job_id, skill_id) VALUES %s "
                        "ON CONFLICT DO NOTHING",
                        pairs,
                    )
        print(f"Tagged {len(pairs)} job-skill links")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
