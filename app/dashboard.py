"""Step 6: skill-trend dashboard. Run with: streamlit run app/dashboard.py"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from db import get_connection  # noqa: E402

st.set_page_config(page_title="Job Market Dashboard", layout="wide")


@st.cache_data(ttl=600)
def query(sql):
    conn = get_connection()
    try:
        return pd.read_sql(sql, conn)
    finally:
        conn.close()


st.title("Job Market Dashboard")

totals = query("""
    SELECT COUNT(*) AS jobs,
           COUNT(DISTINCT company) AS companies,
           ROUND(AVG((salary_min + salary_max) / 2)) AS avg_salary
    FROM jobs
""").iloc[0]
c1, c2, c3 = st.columns(3)
c1.metric("Job postings", int(totals["jobs"]))
c2.metric("Companies", int(totals["companies"]))
c3.metric("Avg salary (where listed)",
          f"${int(totals['avg_salary']):,}" if pd.notnull(totals["avg_salary"]) else "n/a")

st.subheader("Most-demanded skills")
skills = query("""
    SELECT s.name AS skill, COUNT(*) AS postings
    FROM job_skills js JOIN skills s ON s.id = js.skill_id
    GROUP BY s.name ORDER BY postings DESC LIMIT 20
""")
st.bar_chart(skills.set_index("skill"))

left, right = st.columns(2)
with left:
    st.subheader("Top locations")
    locs = query("""
        SELECT location, COUNT(*) AS postings FROM jobs
        WHERE location IS NOT NULL
        GROUP BY location ORDER BY postings DESC LIMIT 15
    """)
    st.bar_chart(locs.set_index("location"))
with right:
    st.subheader("Top hiring companies")
    comps = query("""
        SELECT company, COUNT(*) AS postings FROM jobs
        WHERE company IS NOT NULL
        GROUP BY company ORDER BY postings DESC LIMIT 15
    """)
    st.dataframe(comps, use_container_width=True, hide_index=True)

st.subheader("Postings over time")
daily = query("""
    SELECT DATE(date_posted) AS day, COUNT(*) AS postings FROM jobs
    WHERE date_posted IS NOT NULL GROUP BY day ORDER BY day
""")
if not daily.empty:
    st.line_chart(daily.set_index("day"))

st.subheader("Salary by skill (median midpoint)")
sal = query("""
    SELECT s.name AS skill,
           PERCENTILE_CONT(0.5) WITHIN GROUP
             (ORDER BY (j.salary_min + j.salary_max) / 2) AS median_salary,
           COUNT(*) AS postings
    FROM jobs j
    JOIN job_skills js ON js.job_id = j.id
    JOIN skills s ON s.id = js.skill_id
    WHERE j.salary_min IS NOT NULL AND j.salary_max IS NOT NULL
    GROUP BY s.name HAVING COUNT(*) >= 5
    ORDER BY median_salary DESC
""")
st.dataframe(sal, use_container_width=True, hide_index=True)
