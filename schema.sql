CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS jobs (
    id           SERIAL PRIMARY KEY,
    source       TEXT NOT NULL,
    external_id  TEXT NOT NULL,
    title        TEXT NOT NULL,
    company      TEXT,
    location     TEXT,
    salary_min   NUMERIC,
    salary_max   NUMERIC,
    description  TEXT,
    url          TEXT,
    date_posted  TIMESTAMP,
    fetched_at   TIMESTAMP DEFAULT NOW(),
    UNIQUE (source, external_id)
);

CREATE TABLE IF NOT EXISTS skills (
    id    SERIAL PRIMARY KEY,
    name  TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id    INT REFERENCES jobs(id) ON DELETE CASCADE,
    skill_id  INT REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (job_id, skill_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_date ON jobs(date_posted);
