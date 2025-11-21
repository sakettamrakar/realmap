# CG RERA Extraction, QA, and DB Tools

This repository collects project data from the Chhattisgarh RERA portal, normalizes it to V1 scraper JSON, validates outputs with field-by-field QA, and loads results into Postgres for querying (including a lightweight FastAPI API).

## What is here

- Crawler (`cg_rera_extractor.cli`) with DRY_RUN, LISTINGS_ONLY, and FULL modes.
- QA utilities (`tools/run_field_by_field_qa.py`, `tools/dev_fresh_run_and_qa.py`) to compare detail HTML against normalized JSON.
- DB tooling (`tools/init_db.py`, `tools/load_runs_to_db.py`, `tools/check_db_counts.py`) and a tiny FastAPI app.
- Test suites covering parsing, QA comparison, and system checks.

Repository layout (key folders):

```
cg_rera_extractor/
  browser/      # Browser and session helpers
  config/       # Config models and CLI parsing
  listing/      # Listing scraper + models
  detail/       # Detail page fetchers and preview helpers
  outputs/      # Run artifact writers
  parsing/      # HTML parsing and V1 mapping
  qa/           # Field extraction and comparison utilities
tests/          # Unit and smoke tests
tools/          # CLI helpers (crawl+QA smoke, DB tools, system checks)
```

## Quick setup

1) Python 3.10+, Postgres optional unless loading data or running the API.  
2) Create a virtualenv and install: `python -m venv .venv && .\\.venv\\Scripts\\Activate.ps1 && pip install -r requirements.txt`.  
3) Copy a config: `config.example.yaml` (FULL demo) or `config.phase2.sample.yaml` (safe LISTINGS_ONLY).  
4) If using the DB/API, set `DATABASE_URL` (or edit `db.url` in your config).

## Run the crawler

- Dry run (no browser/network):  
  `python -m cg_rera_extractor.cli --config config.phase2.sample.yaml --mode dry-run`
- Listings only:  
  `python -m cg_rera_extractor.cli --config config.phase2.sample.yaml --mode listings-only`
- Full flow with detail HTML and normalized JSON (manual CAPTCHA required):  
  `python -m cg_rera_extractor.cli --config config.phase2.sample.yaml --mode full`

Outputs land under `<output_base_dir>/runs/run_<timestamp>/` with `listings/`, `raw_html/`, `scraped_json/`, and `run_report.json`.

## QA in a few commands

- One-shot crawl + QA smoke (best default):  
  `python tools/dev_fresh_run_and_qa.py --mode full --config config.debug.yaml`
- QA on an existing run:  
  `python tools/run_field_by_field_qa.py --run-id <run_id> [--limit 10 | --project-key CG-REG-001]`
- QA helper menu:  
  `python tools/test_qa_helper.py list|inspect|qa|compare`

Reports live under `<run>/qa_fields/qa_fields_report.(json|md)`. See `docs/QA_GUIDE.md` for reading the statuses and troubleshooting mismatches.

## Load and verify the database

1) Initialize schema: `python tools/init_db.py`  
2) Load the latest run: `python tools/load_runs_to_db.py --latest`  
3) Show row counts or drill into a project:  
   `python tools/check_db_counts.py [--project-reg <id>]`

Once data is loaded, start the optional API:  
`uvicorn cg_rera_extractor.api.app:app --reload`

Details and troubleshooting live in `docs/DB_GUIDE.md`.

## Health checks and developer workflows

- Fast offline check: `python tools/self_check.py`
- Supervised end-to-end check (crawl + DB verify): `python tools/system_full_check.py`
- Dev smoke (crawl + QA only): `python tools/dev_fresh_run_and_qa.py`

Architecture notes, test strategy, and extension tips are in `docs/DEV_GUIDE.md`.

## Doc map

- AI agent rules: `AI_Instructions.md`
- Developer workflows and architecture: `docs/DEV_GUIDE.md`
- QA tooling and report interpretation: `docs/QA_GUIDE.md`
- Database flow and schema notes: `docs/DB_GUIDE.md`
