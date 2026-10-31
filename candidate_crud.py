"""
HR Candidate CRUD Menu
Run: python candidate_crud.py
Uses candidates.db in the same folder as this script.
"""
from pathlib import Path
import sqlite3
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent
DB_FILE = ROOT / "candidates.db"

FIELDS = [
    "CV File", "Candidate Name", "Email", "Phone", "Match Score (%)",
    "Matched Skills", "Missing / Unclear Requirements", "Evidence Summary",
    "Shortlist Status", "Human Review", "Proposed Interview Date",
    "Proposed Interview Time", "Interview Location", "Calendar Status",
    "Calendar Event Link", "Analysis Notes",
]
EDITABLE_FIELDS = FIELDS[:]  # HR may edit any candidate field.


def connect():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    definitions = ",\n        ".join(f'"{f}" TEXT' for f in FIELDS)
    with connect() as con:
        con.execute(f"""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {definitions},
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        con.execute(
            'CREATE UNIQUE INDEX IF NOT EXISTS idx_candidates_cv_file '
            'ON candidates ("CV File")'
        )
        count = con.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        excel_file = ROOT / "output.xlsx"
        # Import the existing analyzer report once, so HR can use CRUD without
        # paying to rerun the AI analysis just to populate the first database.
        if count == 0 and excel_file.exists():
            try:
                workbook = load_workbook(excel_file, read_only=True, data_only=True)
                worksheet = workbook.active
                headers = [cell.value for cell in next(worksheet.iter_rows(min_row=1, max_row=1))]
                if all(field in headers for field in FIELDS):
                    indexes = [headers.index(field) for field in FIELDS]
                    placeholders = ", ".join("?" for _ in FIELDS)
                    insert_sql = (
                        "INSERT OR IGNORE INTO candidates (" +
                        ", ".join(f'"{field}"' for field in FIELDS) +
                        f") VALUES ({placeholders})"
                    )
                    for excel_row in worksheet.iter_rows(min_row=2, values_only=True):
                        values = ["" if excel_row[i] is None else str(excel_row[i]) for i in indexes]
                        if values[0].strip():
                            con.execute(insert_sql, values)
                workbook.close()
            except Exception as exc:
                print(f"Note: could not import output.xlsx: {exc}")


def print_candidate(row):
    print("\n" + "-" * 60)
    print(f"Candidate ID: {row['id']}")
    for field in FIELDS:
        print(f"{field}: {row[field] or ''}")
    print(f"Created at: {row['created_at']}")
    print(f"Updated at: {row['updated_at']}")
    print("-" * 60)


def list_candidates():
    with connect() as con:
        rows = con.execute(
            'SELECT id, "Candidate Name", Email, "Match Score (%)", "Shortlist Status" '
            'FROM candidates ORDER BY id'
        ).fetchall()
    if not rows:
        print("No candidate records found yet. Run CV_analyzer.py first.")
        return
    print("\nID | Candidate Name | Email | Score | Shortlist Status")
    print("-" * 90)
    for r in rows:
        print(f"{r['id']} | {r['Candidate Name'] or ''} | {r['Email'] or ''} | "
              f"{r['Match Score (%)'] or ''} | {r['Shortlist Status'] or ''}")


def read_candidate():
    try:
        candidate_id = int(input("Enter candidate ID: ").strip())
    except ValueError:
        print("Please enter a numeric ID.")
        return
    with connect() as con:
        row = con.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    if row:
        print_candidate(row)
    else:
        print("Candidate ID not found.")


def create_candidate():
    print("Enter candidate details (CV File is required). Leave other fields blank if unknown.")
    values = {}
    for field in FIELDS:
        if field == "CV File":
            while not values.get(field):
                values[field] = input(f"{field}: ").strip()
                if not values[field]:
                    print("CV File cannot be blank.")
        else:
            values[field] = input(f"{field}: ").strip()
    try:
        with connect() as con:
            columns = ", ".join(f'"{f}"' for f in FIELDS)
            placeholders = ", ".join("?" for _ in FIELDS)
            con.execute(
                f"INSERT INTO candidates ({columns}) VALUES ({placeholders})",
                [values[f] for f in FIELDS],
            )
        print("Candidate created successfully.")
    except sqlite3.IntegrityError:
        print("A candidate with that CV File already exists. Use Update instead.")


def update_candidate():
    try:
        candidate_id = int(input("Enter candidate ID to update: ").strip())
    except ValueError:
        print("Please enter a numeric ID.")
        return
    with connect() as con:
        row = con.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not row:
            print("Candidate ID not found.")
            return
        print_candidate(row)
        print("\nFields:")
        for i, field in enumerate(EDITABLE_FIELDS, start=1):
            print(f"{i}. {field}")
        try:
            choice = int(input("Choose field number to update: ").strip())
            if not 1 <= choice <= len(EDITABLE_FIELDS):
                raise ValueError
        except ValueError:
            print("Invalid field number.")
            return
        field = EDITABLE_FIELDS[choice - 1]
        value = input(f"New value for {field}: ").strip()
        if field == "CV File" and not value:
            print("CV File cannot be blank.")
            return
        try:
            con.execute(
                f'UPDATE candidates SET "{field}" = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (value, candidate_id),
            )
            print("Candidate updated successfully.")
        except sqlite3.IntegrityError:
            print("That CV File is already assigned to another candidate.")


def delete_candidate():
    try:
        candidate_id = int(input("Enter candidate ID to delete: ").strip())
    except ValueError:
        print("Please enter a numeric ID.")
        return
    with connect() as con:
        row = con.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not row:
            print("Candidate ID not found.")
            return
        print_candidate(row)
        confirm = input("Permanently delete this record? Type DELETE to confirm: ").strip()
        if confirm == "DELETE":
            con.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
            print("Candidate deleted.")
        else:
            print("Deletion cancelled.")


def main():
    init_db()
    while True:
        print("""
=== HR Candidate Management (SQLite) ===
1. List candidates
2. Read candidate details
3. Create candidate
4. Update candidate
5. Delete candidate
0. Exit
""")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            list_candidates()
        elif choice == "2":
            read_candidate()
        elif choice == "3":
            create_candidate()
        elif choice == "4":
            update_candidate()
        elif choice == "5":
            delete_candidate()
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Invalid option. Choose 0–5.")


if __name__ == "__main__":
    main()
