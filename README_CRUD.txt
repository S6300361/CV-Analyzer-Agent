CV Analyzer + HR CRUD

Files:
- CV_analyzer.py: analyzes CVs, writes output.xlsx, and upserts candidate records to candidates.db.
- candidate_crud.py: interactive HR menu to list/read/create/update/delete candidate records.
- job_description.txt: job description used by analyzer.
- requirements.txt: Python packages.

Setup:
1. Keep CV_analyzer.py, candidate_crud.py, job_description.txt, requirements.txt, and api.env in the same project folder.
2. Put CV files in CV_Folder_16_Sample_CVs.
3. Ensure api.env has your own valid OPENAI_API_KEY. Do not share or commit api.env.
4. In PowerShell, change to your project folder and install dependencies:
   python -m pip install -r requirements.txt
5. Run the analyzer:
   .\.venv\Scripts\python.exe .\CV_analyzer.py
   (or python CV_analyzer.py if the virtual environment is activated)
6. Run the HR CRUD menu:
   .\.venv\Scripts\python.exe .\candidate_crud.py
7. Use menu options 1–5 to list, read, create, update, or delete records.

Database:
- SQLite database is candidates.db, created automatically.
- Running CV_analyzer.py inserts new CV records and updates existing records using CV File as the unique key.
- HR changes made through CRUD are stored in SQLite. A later analyzer run refreshes the analyzed fields for CVs that are processed again.
- Keep database access restricted to authorized HR staff; it contains personal candidate data.
- CRUD delete requires typing DELETE to confirm.
- Match scores are decision support only; a human recruiter must review candidates before hiring decisions.
