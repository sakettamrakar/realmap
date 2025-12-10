# Quickstart

This guide gets you from clone to a small CG RERA run with data loaded into Postgres and the UI running.

## Prerequisites

- Python 3.10+ (3.11 recommended)
- Node.js (for the frontend)
- PostgreSQL (local or remote) if you plan to load data or run the API

## 1. Clone and install Python dependencies

From the repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
``

## 2. Configure the environment

- Copy a sample config:
  - `config.example.yaml` for a full demo crawl.
  - `config.phase2.sample.yaml` for a safe `LISTINGS_ONLY` run.
- Set `DATABASE_URL` if you will use the DB/API (or edit `db.url` in your config file).

## 3. Run a small crawl + QA

The simplest end-to-end smoke is:

```powershell
python tools/dev_fresh_run_and_qa.py --mode full --config config.debug.yaml
```

This will:

- Run a small crawl.
- Produce HTML + V1 JSON under a new `runs/run_<id>/` directory.
- Generate field-by-field QA reports under `qa_fields/` in that run.

## 4. Load data into Postgres

Initialize the database and load the latest run:

```powershell
python tools/init_db.py
python tools/run_migrations.py
python tools/load_runs_to_db.py --latest
python tools/check_db_counts.py
```

You should see row counts for `projects` and related tables increase after the load.

## 5. Start the API and frontend

From the repo root (with `DATABASE_URL` set):

```powershell
python -m cg_rera_extractor.api.main
```

In another shell for the frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (typically `http://localhost:5173`) to explore projects.

## 6. Where to go next

- For environment and config details, see `installation-setup.md` and `environment-config.md`.
- For scraper internals, see `../03-engineering/code-structure.md`.
- For QA and operational checks, see `../04-operations/monitoring-alerting.md` and `../04-operations/troubleshooting-runbook.md`. 