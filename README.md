# Spend Analyzer

A Python-first **spend / expense analytics** tool. Point it at a transactions
CSV and it returns category, vendor and monthly breakdowns, month-over-month
trends, large-transaction **outliers** and suspected **duplicate payments**
(with the recoverable amount) — exposed as a **FastAPI** service, a **Typer
CLI**, and downloadable **Excel (openpyxl)** and **PDF (reportlab)** reports.
A light React UI is included for uploading a CSV and viewing the results.

Built with the help of AI coding tools (Claude Code) and reviewed/tested by hand.

## Tech stack

- **Core / data:** Python, **Pandas**, **NumPy** — all analytics live in `app/analytics.py`.
- **API:** **FastAPI** + Pydantic, tested with **pytest** (`fastapi.testclient`).
- **Reports:** **openpyxl** (multi-sheet workbook + bar chart) and **reportlab** (PDF).
- **CLI:** **Typer** (`python -m app.cli`).
- **Frontend:** React 18 + Vite (light UI — upload, KPIs, charts, report download).

## What it computes

| Area | Detail |
|---|---|
| Summary | Total / average / median spend, distinct vendors & categories, date range |
| By category | Spend and share-of-total per category |
| By vendor | Top-N vendors by spend |
| By month | Monthly totals + month-over-month % change |
| Outliers | Unusually large transactions via the IQR rule (`Q3 + 1.5·IQR`) |
| Duplicate payments | Same vendor + amount within a time window → recoverable amount |
| Insights | Short auto-generated takeaways |

## Project structure

```
spend_analyzer/
├── backend/
│   ├── app/
│   │   ├── analytics.py     # Pandas/NumPy analytics core
│   │   ├── models.py        # Pydantic response models
│   │   ├── exporters.py     # openpyxl (Excel) + reportlab (PDF)
│   │   ├── main.py          # FastAPI app
│   │   └── cli.py           # Typer CLI
│   ├── data/
│   │   ├── generate_sample.py
│   │   └── sample_expenses.csv
│   ├── tests/               # pytest (analytics + API)
│   ├── requirements.txt
│   └── pyproject.toml
└── frontend/                # React 18 + Vite (light UI)
```

## Run it locally

**Backend** (http://localhost:8000):

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Interactive API docs: http://localhost:8000/docs

**CLI:**

```bash
cd backend
python -m app.cli analyze data/sample_expenses.csv
python -m app.cli analyze data/sample_expenses.csv --excel report.xlsx --pdf report.pdf
python -m app.cli sample --json
```

**Tests:**

```bash
cd backend && pytest -q
```

**Frontend** (http://localhost:5173):

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies `/api` to the backend. Click **Load sample data** to try
it without uploading anything.

## Input format

A CSV with at least these columns (extra columns such as `department` are kept):

```csv
date,amount,category,vendor,department
2026-04-03,3918.68,Software,Atlassian,Engineering
```

## API

| Method & path | Purpose |
|---|---|
| `GET /api/health` | Liveness probe |
| `GET /api/sample` | Analytics for the bundled sample dataset |
| `POST /api/analyze` | Analytics for an uploaded CSV (multipart `file`) |
| `POST /api/report?fmt=excel\|pdf` | Download an Excel or PDF report for an uploaded CSV |
