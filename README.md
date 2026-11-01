# CV Analyzer Agent

An AI-assisted CV screening project that compares candidate resumes with
a job description, stores screening results in SQLite, and displays
candidate insights in a Streamlit dashboard.

## Overview

The project supports an initial recruitment-screening workflow: 
1. Reads CV files from the configured input folder. 
2. Evaluates candidate information against the job requirements configured in the analyzer.
Uses the Google Gemini API to assist with resume analysis. 
4. Stores screening records in a local SQLite database. 
5. Displays candidate metrics and screening information in a Streamlit dashboard.

**Important:** AI-generated scores and recommendations are
decision-support information only. A human recruiter must review
candidates and make all hiring decisions.

## Features

-   AI-assisted CV analysis using Google Gemini.
-   Job-description matching using the criteria configured in the
    project.
-   Local candidate record storage with SQLite.
-   Candidate database operations in `candidate_crud.py`.
-   Streamlit dashboard with metrics, score visualizations, status
    summaries, filters, search, and candidate details.
-   Human review of screening results.

## Project Structure

``` text
CV_Analyzer_Agent/
├── CV_analyzer.py           # CV analysis workflow
├── candidate_crud.py        # SQLite candidate database operations
├── dashboard.py             # Streamlit dashboard
├── job_description.txt      # Job requirements
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
├── .gitignore               # Excludes local/private files
├── api.env                  # Local API configuration (keep private)
├── candidates.db            # Local candidate database (keep private)
├── CV_Folder_16_Sample_CVs/ # Local CV files (keep private)
└── .venv/                   # Python virtual environment (keep private)
```

The local/private items may not appear in the GitHub repository because
they are excluded by `.gitignore`.

## Technologies

-   Python
-   Google Gemini API
-   SQLite
-   Streamlit
-   Pandas
-   Git and GitHub

## Requirements

-   Python installed on your computer.
-   A Google Gemini API key.
-   The dependencies listed in `requirements.txt`.

## Setup

### 1. Clone the repository

``` bash
git clone https://github.com/S6300361/CV-Analyzer-Agent.git
cd CV-Analyzer-Agent
```

### 2. Create and activate a virtual environment

For Windows PowerShell:

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation is blocked, you can run the environment's Python
executable directly:

``` powershell
.\.venv\Scripts\python.exe --version
```

### 3. Install dependencies

``` powershell
python -m pip install -r requirements.txt
```

### 4. Configure the Gemini API

Create a local file named `api.env` in the project root. Add your own
credentials and a Gemini model available to your account:

``` env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=YOUR_AVAILABLE_GEMINI_MODEL
ENABLE_CALENDAR_SCHEDULING=false
```

Replace the placeholders with your own values. Never commit `api.env`,
publish your API key, or share it in screenshots.

### 5. Configure the job and CV inputs

-   Update `job_description.txt` with the role requirements.
-   Place CV files you are authorized to process in the input folder
    configured by `CV_analyzer.py`.
-   Check `CV_analyzer.py` for the supported file formats and
    input-folder settings.

## Run the CV Analyzer

From the project root, with the virtual environment activated:

``` powershell
python CV_analyzer.py
```

Alternatively:

``` powershell
.\.venv\Scripts\python.exe CV_analyzer.py
```

## Run the Dashboard

``` powershell
python -m streamlit run dashboard.py
```

Alternatively:

``` powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard.py
```

Open the local URL printed by Streamlit. It is commonly:

``` text
http://localhost:8501
```

## Database

Candidate screening records are stored in the local SQLite database
`candidates.db`. The `candidate_crud.py` module contains
database-related operations.

Keep this database private because it may contain personal candidate
information.

## Privacy and Responsible Use

-   Process CVs only when you are authorized to do so.
-   Treat AI scores and summaries as preliminary assistance, not
    objective measures of a person's ability.
-   Use consistent, job-related criteria and human review.
-   Do not upload candidate CVs, personal data, database files, API
    keys, or environment files to a public repository.
-   Keep `api.env`, `candidates.db`, the CV folder, and `.venv` excluded
    from Git.
-   Check repository visibility and access permissions before sharing
    the project.

## Troubleshooting

**Gemini API or model error** - Check that `api.env` exists in the
project root. - Confirm that the API key is valid and that the
configured model is available to your account. - Do not share your API
key when asking for help.

**Missing dependencies**

``` powershell
python -m pip install -r requirements.txt
```

**Dashboard does not start** - Confirm that Streamlit is installed. -
Run the command from the project root. - Check the terminal output for
the specific error.

**No candidates appear** - Confirm that the analyzer has processed
CVs. - Confirm that the dashboard is connected to the expected SQLite
database.

## Author

Developed as a learning project exploring Python, AI-assisted resume
analysis, SQLite database management, and Streamlit dashboards.
https://hrassist.streamlit.app/
