
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

# Import shared database helpers and field definitions from candidate_crud.py
from candidate_crud import connect, init_db, FIELDS

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "candidates.db"

st.set_page_config(page_title="CV Analyzer Dashboard", page_icon="📄", layout="wide")
st.title("📄 CV Analyzer Dashboard")
st.caption("Candidate screening overview • Connected directly to SQLite")

# Initialize the existing database using the CRUD module.
try:
    init_db()
except Exception as exc:
    st.error(f"Could not initialize the candidates database: {exc}")
    st.stop()


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

# Keep the dashboard usable even when there are no candidates yet.
if df.empty:
    st.warning("No candidate records found. Run CV_analyzer.py or add a candidate below.")

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
        | filtered["CV File"].fillna("").str.lower().str.contains(q, na=False)
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


# ============================================================
# CRUD OPERATIONS — added below the original dashboard
# ============================================================

st.divider()
st.header("Candidate CRUD Operations")
st.caption("Create, read, update, and delete candidate records in the same SQLite database.")

# READ: View every candidate independently of the dashboard filters.
with st.expander("View all candidate records", expanded=False):
    with connect() as con:
        all_candidates = pd.read_sql_query(
            "SELECT * FROM candidates ORDER BY id DESC", con
        )
    st.dataframe(all_candidates, use_container_width=True, hide_index=True)


# CREATE: Add a candidate using a Streamlit form.
with st.expander("Add a new candidate", expanded=False):
    with st.form("create_candidate_form"):
        new_values = {}

        new_values["CV File"] = st.text_input("CV File *")

        left, right = st.columns(2)
        with left:
            new_values["Candidate Name"] = st.text_input("Candidate Name")
            new_values["Email"] = st.text_input("Email")
            new_values["Phone"] = st.text_input("Phone")
            new_values["Match Score (%)"] = st.text_input("Match Score (%)")

        with right:
            new_values["Shortlist Status"] = st.selectbox(
                "Shortlist Status",
                ["Not shortlisted", "Shortlisted", "Pending review"]
            )
            new_values["Human Review"] = st.selectbox(
                "Human Review", ["Yes", "No", "Pending"]
            )
            new_values["Proposed Interview Date"] = st.text_input(
                "Proposed Interview Date"
            )
            new_values["Proposed Interview Time"] = st.text_input(
                "Proposed Interview Time"
            )

        new_values["Matched Skills"] = st.text_area("Matched Skills")
        new_values["Missing / Unclear Requirements"] = st.text_area(
            "Missing / Unclear Requirements"
        )
        new_values["Evidence Summary"] = st.text_area("Evidence Summary")
        new_values["Analysis Notes"] = st.text_area("Analysis Notes")
        new_values["Interview Location"] = st.text_input("Interview Location")
        new_values["Calendar Status"] = st.text_input("Calendar Status")
        new_values["Calendar Event Link"] = st.text_input("Calendar Event Link")

        create_submitted = st.form_submit_button("Create candidate")

    if create_submitted:
        if not new_values["CV File"].strip():
            st.error("CV File is required.")
        else:
            # Store a numeric score as entered; leave unknown scores blank.
            score_text = new_values["Match Score (%)"].strip()
            if score_text:
                try:
                    score_number = float(score_text)
                    if not 0 <= score_number <= 100:
                        raise ValueError
                    new_values["Match Score (%)"] = str(score_number)
                except ValueError:
                    st.error("Match Score (%) must be a number from 0 to 100.")
                    st.stop()

            try:
                with connect() as con:
                    columns = ", ".join(f'"{field}"' for field in FIELDS)
                    placeholders = ", ".join("?" for _ in FIELDS)
                    con.execute(
                        f"INSERT INTO candidates ({columns}) VALUES ({placeholders})",
                        [new_values.get(field, "") for field in FIELDS],
                    )

                st.success("Candidate created successfully.")
                st.cache_data.clear()
                st.rerun()

            except sqlite3.IntegrityError:
                st.error("A candidate with this CV File already exists.")
            except Exception as exc:
                st.error(f"Could not create candidate: {exc}")


# UPDATE: Select a candidate and edit its fields.
with st.expander("Update a candidate", expanded=False):
    with connect() as con:
        candidates_for_update = con.execute(
            'SELECT id, "Candidate Name", "CV File" '
            'FROM candidates ORDER BY id DESC'
        ).fetchall()

    if not candidates_for_update:
        st.info("There are no candidates to update.")
    else:
        update_options = {
            f"{row['Candidate Name'] or 'Unnamed candidate'} — "
            f"{row['CV File']} (ID {row['id']})": row["id"]
            for row in candidates_for_update
        }

        selected_update = st.selectbox(
            "Choose candidate to update",
            list(update_options.keys()),
            key="update_candidate_selector",
        )
        update_id = update_options[selected_update]

        with connect() as con:
            existing = con.execute(
                "SELECT * FROM candidates WHERE id = ?", (update_id,)
            ).fetchone()

        with st.form("update_candidate_form"):
            updated_values = {}
            for field in FIELDS:
                current_value = existing[field] or ""
                updated_values[field] = st.text_input(
                    field,
                    value=str(current_value),
                    key=f"update_{update_id}_{field}",
                )

            update_submitted = st.form_submit_button("Save changes")

        if update_submitted:
            if not updated_values["CV File"].strip():
                st.error("CV File cannot be blank.")
            else:
                score_text = updated_values["Match Score (%)"].strip()
                score_valid = True

                if score_text:
                    try:
                        score_number = float(score_text)
                        if not 0 <= score_number <= 100:
                            raise ValueError
                        updated_values["Match Score (%)"] = str(score_number)
                    except ValueError:
                        score_valid = False
                        st.error("Match Score (%) must be a number from 0 to 100.")

                if score_valid:
                    try:
                        assignments = ", ".join(
                            f'"{field}" = ?' for field in FIELDS
                        )
                        with connect() as con:
                            con.execute(
                                f"UPDATE candidates SET {assignments}, "
                                "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                                [updated_values[field] for field in FIELDS]
                                + [update_id],
                            )

                        st.success("Candidate updated successfully.")
                        st.cache_data.clear()
                        st.rerun()

                    except sqlite3.IntegrityError:
                        st.error("That CV File is already assigned to another candidate.")
                    except Exception as exc:
                        st.error(f"Could not update candidate: {exc}")


# DELETE: Require explicit confirmation before permanently deleting a record.
with st.expander("Delete a candidate", expanded=False):
    with connect() as con:
        candidates_for_delete = con.execute(
            'SELECT id, "Candidate Name", "CV File" '
            'FROM candidates ORDER BY id DESC'
        ).fetchall()

    if not candidates_for_delete:
        st.info("There are no candidates to delete.")
    else:
        delete_options = {
            f"{row['Candidate Name'] or 'Unnamed candidate'} — "
            f"{row['CV File']} (ID {row['id']})": row["id"]
            for row in candidates_for_delete
        }

        selected_delete = st.selectbox(
            "Choose candidate to delete",
            list(delete_options.keys()),
            key="delete_candidate_selector",
        )
        delete_id = delete_options[selected_delete]

        confirm_delete = st.checkbox(
            "I confirm that I want to permanently delete this candidate record.",
            key="confirm_candidate_delete",
        )

        if st.button("Delete candidate", type="secondary"):
            if not confirm_delete:
                st.warning("Please confirm before deleting.")
            else:
                try:
                    with connect() as con:
                        con.execute(
                            "DELETE FROM candidates WHERE id = ?", (delete_id,)
                        )

                    st.success("Candidate deleted successfully.")
                    st.cache_data.clear()
                    st.rerun()

                except Exception as exc:
                    st.error(f"Could not delete candidate: {exc}")