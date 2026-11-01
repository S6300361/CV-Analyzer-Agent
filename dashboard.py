
from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st
import candidate_crud as crud


# --------------------------------------------------
# 1. PAGE CONFIGURATION AND DATABASE INITIALIZATION
# --------------------------------------------------

st.set_page_config(
    page_title="CV Analyzer - HR Dashboard",
    page_icon="📄",
    layout="wide",
)

ROOT = Path(__file__).resolve().parent
DB_FILE = ROOT / "candidates.db"

# Initialize the database using your existing CRUD module.
crud.init_db()


# --------------------------------------------------
# 2. DATABASE HELPER FUNCTIONS
# --------------------------------------------------

def get_all_candidates():
    """Return all candidates from the SQLite database."""
    with crud.connect() as con:
        return pd.read_sql_query(
            'SELECT * FROM candidates ORDER BY id DESC',
            con,
        )


def get_candidate_by_id(candidate_id):
    """Return one candidate using its database ID."""
    with crud.connect() as con:
        row = con.execute(
            "SELECT * FROM candidates WHERE id = ?",
            (candidate_id,),
        ).fetchone()

    return dict(row) if row else None


def validate_candidate(values):
    """Validate required fields and the optional match score."""
    if not values.get("CV File", "").strip():
        return "CV File is required."

    score = values.get("Match Score (%)", "").strip()

    if score:
        try:
            numeric_score = float(score)
        except ValueError:
            return "Match Score (%) must be a number between 0 and 100."

        if not 0 <= numeric_score <= 100:
            return "Match Score (%) must be between 0 and 100."

    return None


def create_candidate_record(values):
    """Insert a new candidate using the fields in candidate_crud.py."""
    columns = ", ".join(f'"{field}"' for field in crud.FIELDS)
    placeholders = ", ".join("?" for _ in crud.FIELDS)

    sql = (
        f"INSERT INTO candidates ({columns}) "
        f"VALUES ({placeholders})"
    )

    with crud.connect() as con:
        con.execute(
            sql,
            [values.get(field, "").strip() for field in crud.FIELDS],
        )


def update_candidate_record(candidate_id, values):
    """Update a candidate and refresh the updated_at timestamp."""
    assignments = ", ".join(
        f'"{field}" = ?' for field in crud.EDITABLE_FIELDS
    )

    sql = (
        f"UPDATE candidates SET {assignments}, "
        "updated_at = CURRENT_TIMESTAMP WHERE id = ?"
    )

    parameters = [
        values.get(field, "").strip()
        for field in crud.EDITABLE_FIELDS
    ]
    parameters.append(candidate_id)

    with crud.connect() as con:
        con.execute(sql, parameters)


def delete_candidate_record(candidate_id):
    """Permanently delete a candidate by ID."""
    with crud.connect() as con:
        con.execute(
            "DELETE FROM candidates WHERE id = ?",
            (candidate_id,),
        )


# --------------------------------------------------
# 3. REUSABLE FORM FIELD WIDGET
# --------------------------------------------------

MULTILINE_FIELDS = {
    "Matched Skills",
    "Missing / Unclear Requirements",
    "Evidence Summary",
    "Analysis Notes",
}


def render_candidate_fields(fields, prefix, existing=None):
    """
    Display form fields and return their entered values.
    Existing values are used when editing a candidate.
    """
    values = {}

    for field in fields:
        default_value = ""

        if existing:
            saved_value = existing.get(field, "")
            default_value = (
                "" if saved_value is None else str(saved_value)
            )

        widget_key = f"{prefix}_{field}"

        if field in MULTILINE_FIELDS:
            values[field] = st.text_area(
                field,
                value=default_value,
                key=widget_key,
                height=100,
            )
        else:
            values[field] = st.text_input(
                field,
                value=default_value,
                key=widget_key,
            )

    return values


# --------------------------------------------------
# 4. DASHBOARD HEADER AND NAVIGATION
# --------------------------------------------------

st.title("📄 CV Analyzer — HR Dashboard")
st.caption(
    "Manage candidate records, review CV analysis, "
    "and maintain interview details."
)

st.sidebar.title("HR Navigation")

page = st.sidebar.radio(
    "Choose an operation",
    [
        "Dashboard & View",
        "Create Candidate",
        "Update Candidate",
        "Delete Candidate",
    ],
)

st.sidebar.divider()
st.sidebar.caption(f"Database: {DB_FILE.name}")


# --------------------------------------------------
# 5. DASHBOARD: READ, SEARCH, FILTER AND VIEW
# --------------------------------------------------

if page == "Dashboard & View":
    st.header("Candidate Overview")

    try:
        df = get_all_candidates()
    except (sqlite3.Error, pd.errors.DatabaseError) as exc:
        st.error(f"Could not read the candidates database: {exc}")
        st.stop()

    total_candidates = len(df)

    if "Shortlist Status" in df.columns:
        statuses = (
            df["Shortlist Status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )
        shortlisted_count = statuses.str.contains(
            "shortlist", regex=False
        ).sum()
    else:
        shortlisted_count = 0

    if "Human Review" in df.columns:
        review_values = (
            df["Human Review"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )
        review_count = review_values.isin(
            ["yes", "true", "required", "needed", "pending"]
        ).sum()
    else:
        review_count = 0

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Candidates", total_candidates)
    col2.metric("Shortlisted", int(shortlisted_count))
    col3.metric("Flagged for Human Review", int(review_count))

    st.divider()
    st.subheader("Search and Filter Candidates")

    search_text = st.text_input(
        "Search by name, email, CV filename or phone",
        placeholder="Enter a candidate name or keyword...",
    )

    if "Shortlist Status" in df.columns:
        all_statuses = (
            df["Shortlist Status"]
            .fillna("")
            .astype(str)
            .str.strip()
        )
        status_options = ["All"] + sorted(
            status for status in all_statuses.unique() if status
        )

        selected_status = st.selectbox(
            "Filter by shortlist status",
            status_options,
        )
    else:
        selected_status = "All"

    filtered_df = df.copy()

    if search_text.strip():
        searchable_columns = [
            column
            for column in [
                "Candidate Name",
                "Email",
                "CV File",
                "Phone",
            ]
            if column in filtered_df.columns
        ]

        if searchable_columns:
            mask = pd.Series(False, index=filtered_df.index)

            for column in searchable_columns:
                mask |= (
                    filtered_df[column]
                    .fillna("")
                    .astype(str)
                    .str.contains(
                        search_text.strip(),
                        case=False,
                        regex=False,
                    )
                )

            filtered_df = filtered_df[mask]

    if selected_status != "All":
        filtered_df = filtered_df[
            filtered_df["Shortlist Status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq(selected_status)
        ]

    preferred_columns = [
        "id",
        "Candidate Name",
        "Email",
        "Phone",
        "Match Score (%)",
        "Matched Skills",
        "Shortlist Status",
        "Human Review",
        "Proposed Interview Date",
        "Proposed Interview Time",
    ]

    visible_columns = [
        column
        for column in preferred_columns
        if column in filtered_df.columns
    ]

    st.subheader(f"Candidate Records ({len(filtered_df)})")

    if filtered_df.empty:
        st.info("No candidates match your search or filter.")
    else:
        st.dataframe(
            filtered_df[visible_columns],
            use_container_width=True,
            hide_index=True,
        )

        csv_data = filtered_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download filtered candidates as CSV",
            data=csv_data,
            file_name="filtered_candidates.csv",
            mime="text/csv",
        )

    st.divider()
    st.subheader("View Full Candidate Details")

    if not df.empty:
        candidate_options = df.to_dict("records")

        selected_candidate_id = st.selectbox(
            "Select a candidate",
            options=[row["id"] for row in candidate_options],
            format_func=lambda candidate_id: next(
                (
                    f'ID {row["id"]} — '
                    f'{row.get("Candidate Name") or "Unnamed"} '
                    f'({row.get("CV File") or "No filename"})'
                    for row in candidate_options
                    if row["id"] == candidate_id
                ),
                f"ID {candidate_id}",
            ),
            key="view_candidate_id",
        )

        candidate = get_candidate_by_id(selected_candidate_id)

        if candidate:
            for field in crud.FIELDS:
                value = candidate.get(field, "")
                st.write(
                    f"**{field}:** "
                    f"{value if value not in (None, '') else 'Not provided'}"
                )

            st.caption(f"Database record ID: {candidate['id']}")

            if candidate.get("created_at"):
                st.caption(f"Created: {candidate['created_at']}")

            if candidate.get("updated_at"):
                st.caption(f"Last updated: {candidate['updated_at']}")
    else:
        st.info("No candidate records are available yet.")


# --------------------------------------------------
# 6. CREATE CANDIDATE
# --------------------------------------------------

elif page == "Create Candidate":
    st.header("Create a Candidate Record")

    st.write(
        "Enter the candidate details below. "
        "The CV filename must be unique."
    )

    with st.form("create_candidate_form"):
        values = render_candidate_fields(
            crud.FIELDS,
            prefix="create",
        )

        submitted = st.form_submit_button(
            "Create Candidate",
            type="primary",
        )

    if submitted:
        error = validate_candidate(values)

        if error:
            st.error(error)
        else:
            try:
                create_candidate_record(values)
                st.success("Candidate record created successfully.")
                st.rerun()

            except sqlite3.IntegrityError:
                st.error(
                    "A candidate with this CV File already exists. "
                    "Please use a unique filename."
                )

            except sqlite3.Error as exc:
                st.error(f"Database error: {exc}")


# --------------------------------------------------
# 7. UPDATE CANDIDATE
# --------------------------------------------------

elif page == "Update Candidate":
    st.header("Update a Candidate Record")

    df = get_all_candidates()

    if df.empty:
        st.info("There are no candidates to update.")
    else:
        candidate_options = df.to_dict("records")

        selected_candidate_id = st.selectbox(
            "Select the candidate to update",
            options=[row["id"] for row in candidate_options],
            format_func=lambda candidate_id: next(
                (
                    f'ID {row["id"]} — '
                    f'{row.get("Candidate Name") or "Unnamed"} '
                    f'({row.get("CV File") or "No filename"})'
                    for row in candidate_options
                    if row["id"] == candidate_id
                ),
                f"ID {candidate_id}",
            ),
            key="update_candidate_id",
        )

        existing = get_candidate_by_id(selected_candidate_id)

        if existing:
            st.caption(
                "Edit the fields below. The existing values are "
                "pre-filled; leave a field unchanged to keep its value."
            )

            with st.form("update_candidate_form"):
                values = render_candidate_fields(
                    crud.EDITABLE_FIELDS,
                    prefix=f"update_{selected_candidate_id}",
                    existing=existing,
                )

                submitted = st.form_submit_button(
                    "Save Changes",
                    type="primary",
                )

            if submitted:
                error = validate_candidate(values)

                if error:
                    st.error(error)
                else:
                    try:
                        update_candidate_record(
                            selected_candidate_id,
                            values,
                        )
                        st.success(
                            "Candidate record updated successfully."
                        )
                        st.rerun()

                    except sqlite3.IntegrityError:
                        st.error(
                            "Another record already uses this CV File. "
                            "Please enter a unique filename."
                        )

                    except sqlite3.Error as exc:
                        st.error(f"Database error: {exc}")


# --------------------------------------------------
# 8. DELETE CANDIDATE
# --------------------------------------------------

elif page == "Delete Candidate":
    st.header("Delete a Candidate Record")

    st.warning(
        "Deleting a record is permanent. Confirm the correct candidate "
        "before proceeding."
    )

    df = get_all_candidates()

    if df.empty:
        st.info("There are no candidates to delete.")
    else:
        candidate_options = df.to_dict("records")

        selected_candidate_id = st.selectbox(
            "Select the candidate to delete",
            options=[row["id"] for row in candidate_options],
            format_func=lambda candidate_id: next(
                (
                    f'ID {row["id"]} — '
                    f'{row.get("Candidate Name") or "Unnamed"} '
                    f'({row.get("CV File") or "No filename"})'
                    for row in candidate_options
                    if row["id"] == candidate_id
                ),
                f"ID {candidate_id}",
            ),
            key="delete_candidate_id",
        )

        candidate = get_candidate_by_id(selected_candidate_id)

        if candidate:
            st.subheader("Selected Candidate")

            st.write(
                f'**Candidate Name:** '
                f'{candidate.get("Candidate Name") or "Not provided"}'
            )
            st.write(
                f'**Email:** {candidate.get("Email") or "Not provided"}'
            )
            st.write(
                f'**CV File:** {candidate.get("CV File") or "Not provided"}'
            )
            st.write(
                f'**Match Score:** '
                f'{candidate.get("Match Score (%)") or "Not provided"}'
            )

            confirm_delete = st.checkbox(
                "I confirm that I want to permanently delete this record.",
                key=f"confirm_delete_{selected_candidate_id}",
            )

            if st.button(
                "Delete Candidate Permanently",
                type="primary",
                disabled=not confirm_delete,
            ):
                try:
                    delete_candidate_record(selected_candidate_id)
                    st.success("Candidate record deleted successfully.")
                    st.rerun()

                except sqlite3.Error as exc:
                    st.error(f"Could not delete the candidate: {exc}")


# --------------------------------------------------
# 9. FOOTER
# --------------------------------------------------

st.sidebar.divider()
st.sidebar.caption("CV Analyzer Agent | HR Management")