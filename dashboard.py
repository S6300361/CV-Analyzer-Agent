"""
CV Analyzer Dashboard
Reads candidates directly from candidates.db (SQLite).

Run from your project folder:
    .\\.venv\\Scripts\\python.exe -m streamlit run dashboard.py
"""
from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "candidates.db"

st.set_page_config(page_title="CV Analyzer Dashboard", page_icon="📄", layout="wide")
st.title("📄 CV Analyzer Dashboard")
st.caption("Candidate screening overview • Connected directly to SQLite")

@st.cache_data(ttl=10)
def load_data(path):
    with sqlite3.connect(path) as conn:
        return pd.read_sql_query("SELECT * FROM candidates ORDER BY id DESC", conn)

if not DB_PATH.exists():
    st.error(f"Database not found: {DB_PATH}")
    st.info("Save dashboard.py in the same folder as candidates.db.")
    st.stop()

try:
    df = load_data(str(DB_PATH))
except Exception as exc:
    st.error(f"Could not load the candidates table: {exc}")
    st.stop()

if df.empty:
    st.warning("No candidate records found. Run CV_analyzer.py first.")
    st.stop()

required = ["id", "CV File", "Candidate Name", "Email", "Phone",
            "Match Score (%)", "Matched Skills", "Missing / Unclear Requirements",
            "Evidence Summary", "Shortlist Status", "Human Review", "Analysis Notes"]
missing = [name for name in required if name not in df.columns]
if missing:
    st.error(f"Database is missing expected columns: {missing}")
    st.stop()

df["Score"] = pd.to_numeric(df["Match Score (%)"], errors="coerce")
df["Candidate Name"] = df["Candidate Name"].fillna("Unnamed candidate").astype(str)
df["Shortlist Status"] = df["Shortlist Status"].fillna("Unknown").astype(str)

st.sidebar.header("Filters")
statuses = sorted(df["Shortlist Status"].unique().tolist())
chosen_statuses = st.sidebar.multiselect("Shortlist status", statuses, default=statuses)
minimum_score = st.sidebar.slider("Minimum match score", 0, 100, 0)
search = st.sidebar.text_input("Search candidate or CV filename")

filtered = df[df["Shortlist Status"].isin(chosen_statuses)].copy()
filtered = filtered[filtered["Score"].fillna(-1) >= minimum_score]
if search.strip():
    q = search.strip().lower()
    filtered = filtered[
        filtered["Candidate Name"].str.lower().str.contains(q, na=False)
        | filtered["CV File"].str.lower().str.contains(q, na=False)
    ]

scores = df["Score"].dropna()
average = scores.mean() if not scores.empty else 0
shortlisted = int(df["Shortlist Status"].str.lower().eq("shortlisted").sum())
review_flags = int(df["Human Review"].fillna("").astype(str).str.contains(
    "yes|review|pending", case=False, regex=True).sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total candidate records", len(df))
c2.metric("Average match score", f"{average:.1f}%")
c3.metric("Shortlisted", shortlisted)
c4.metric("Human review flags", review_flags)

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("Candidate match scores")
    chart = filtered[["Candidate Name", "Score"]].dropna().sort_values("Score")
    if chart.empty:
        st.info("No scored candidates match these filters.")
    else:
        st.bar_chart(chart.set_index("Candidate Name")["Score"])
with right:
    st.subheader("Shortlist status distribution")
    counts = filtered["Shortlist Status"].value_counts()
    if counts.empty:
        st.info("No candidates match these filters.")
    else:
        st.bar_chart(counts)

st.divider()
st.subheader(f"Candidate records ({len(filtered)} shown)")
st.dataframe(
    filtered[["id", "Candidate Name", "CV File", "Match Score (%)",
              "Shortlist Status", "Human Review"]],
    use_container_width=True,
    hide_index=True,
)

st.subheader("Candidate details")
options = {
    f"{row['Candidate Name']} — {row['CV File']} (ID {row['id']})": int(row["id"])
    for _, row in filtered.iterrows()
}
if options:
    label = st.selectbox("Select a candidate", list(options.keys()))
    record = df.loc[df["id"] == options[label]].iloc[0]
    a, b = st.columns(2)
    with a:
        st.markdown("**Contact information**")
        st.write("Email:", record["Email"] or "Not provided")
        st.write("Phone:", record["Phone"] or "Not provided")
        st.markdown("**Matched skills**")
        st.write(record["Matched Skills"] or "Not provided")
        st.markdown("**Missing / unclear requirements**")
        st.write(record["Missing / Unclear Requirements"] or "Not provided")
    with b:
        st.markdown("**Evidence summary**")
        st.write(record["Evidence Summary"] or "Not provided")
        st.markdown("**Analysis notes**")
        st.write(record["Analysis Notes"] or "Not provided")
        st.write("Human review:", record["Human Review"] or "Not specified")
else:
    st.info("No candidates match the selected filters.")

st.caption(
    "AI-generated scores are screening aids only. A human reviewer must verify "
    "the CV evidence and make all hiring decisions."
)
if st.button("Refresh dashboard"):
    st.cache_data.clear()
    st.rerun()

st.caption(f"SQLite database: {DB_PATH}")
