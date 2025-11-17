# User Guide – CG RERA Extraction & API

## 1. What this project is
This repository provides a CG RERA (Chhattisgarh Real Estate Regulatory Authority) data extraction framework. It automates collection of project listings and details from the CG RERA site with a small amount of manual assistance for CAPTCHA solving. Outputs include structured run folders containing raw HTML, raw-extracted JSON, normalized V1 JSON, and machine-readable run reports. Phase 3 adds an optional Postgres-backed database layer plus a read-only FastAPI service to explore loaded project data. The typical flow is: run a crawl → inspect run outputs → (optionally) load V1 JSON into the database → (optionally) query projects via the API.

## 2. Prerequisites & Setup
- **Python**: 3.10+ recommended.
- **Git**: to clone the repository.
- **Postgres**: only required if you plan to load data into a database or run the API against Postgres (SQLite is used for quick checks in some tools).
- **Virtual environment**: recommended via `python -m venv .venv` (or your preferred tool).

Steps:
1. Clone: `git clone <repo-url>` then `cd realmap`.
2. Create & activate venv:
   - Linux/macOS: `python -m venv .venv && source .venv/bin/activate`
   - Windows (PowerShell): `python -m venv .venv; .\.venv\Scripts\Activate.ps1`
3. Install dependencies: `pip install -r requirements.txt` (or `pip install -e .` for editable installs).

### Configuration & environment
- **Config files**: start from `config.example.yaml` (FULL mode demo) or `config.phase2.sample.yaml` (safe, limited LISTINGS_ONLY run). Copy and edit as needed.
- **Key settings**:
  - `run.mode`: `DRY_RUN`, `LISTINGS_ONLY`, or `FULL`.
  - `run.output_base_dir`: base folder for outputs; runs are stored under `<output_base_dir>/runs/`.
  - `run.search_filters`: districts/statuses/project_types to search.
  - Safety caps: `max_search_combinations`, `max_total_listings`.
  - `browser.headless`: set to `false` for easier manual CAPTCHA solving.
  - `db.url`: Postgres URL (optional for DB/API workflows).
- **Environment variables**:
  - `DATABASE_URL` can override `db.url` for DB tools/API.
  - Jira-related env vars exist but are **not required** for extraction/DB/API flows.

## 3. Quick Health Check (recommended first steps)
1. Run tests (optional but useful): `pytest` (expect “passed” summary).
2. Run the offline self-check: `python tools/self_check.py`.
   - Success shows lines like `... PASS` and a final summary with zero failures.
   - Warnings are informational unless reported as errors; errors will exit non-zero.

## 4. Running the Extractor (Crawler) – From Zero to First Real Run
Run from the repo root with a chosen config file.

**Modes**
- **DRY_RUN** – plans searches only; no browser, no network. Good for verifying filters and caps.
- **LISTINGS_ONLY** – fetches listing pages and saves listing JSON/HTML; skips detail pages.
- **FULL** – end-to-end: listings → detail HTML → raw extraction → normalized V1 JSON.

**Example commands (using sample config)**
- DRY_RUN: `python -m cg_rera_extractor.cli --config config.phase2.sample.yaml --mode dry-run`
- LISTINGS_ONLY: `python -m cg_rera_extractor.cli --config config.phase2.sample.yaml --mode listings-only`
- FULL: `python -m cg_rera_extractor.cli --config config.phase2.sample.yaml --mode full`

**Manual CAPTCHA step**
- A browser window opens. Solve the CAPTCHA, click **Search**, then press ENTER in the terminal when prompted. The run resumes after you confirm.

**Where outputs go**
- Each run is stored under `<output_base_dir>/runs/run_<timestamp>_<id>/`.
- The latest run has the most recent timestamp; list directories in `<output_base_dir>/runs` to find it.

## 5. Understanding Run Outputs & Checking What Worked
Typical structure (under `<output_base_dir>/runs/run_<id>/`):
- `listings/`: listing HTML snapshots and parsed listing JSON per district/status.
- `raw_html/`: detail page HTML files (FULL mode).
- `raw_extracted/`: raw field/section JSON extracted from each detail page (FULL mode).
- `scraped_json/`: normalized V1 project JSON (FULL mode).
- `run_report.json`: machine-readable summary (mode, filters, counts, warnings/errors).

Quick checks:
- Open `run_report.json` and review counts for `listings_parsed`, `details_fetched`, `projects_mapped`, plus `warnings`/`errors` arrays.
- Confirm `listings/` contains at least one listing JSON file.
- In FULL runs, verify `scraped_json/` has at least one `.v1.json` file and `raw_html/` contains matching HTML.
- Ideally, `run_report.json` shows non-zero counts and no fatal errors.

## 6. Loading Data into the Database (optional but important)
Prerequisites: running Postgres instance (use the shared `postgresql://postgres:betsson@123@localhost:5432/realmapdb` URL unless you have overrides). Set it in your config (`db.url`) or via `DATABASE_URL`.

Steps:
1. Initialize schema: `python tools/init_db.py` (uses config-provided URL or `DATABASE_URL`).
2. Load a specific run: `python tools/load_runs_to_db.py --run-id <run_id>` (defaults to `./runs`; add `--runs-dir <path>` if different). To load all runs under a folder: `python tools/load_runs_to_db.py --runs-dir <path>`.
3. Verify with SQL (e.g., `SELECT COUNT(*) FROM projects;`) using your preferred SQL client. A populated `projects` table confirms success.

## 7. Running the Read-only API & Testing It
Start the FastAPI app (requires DB URL pointing at a database with loaded projects):
- `uvicorn cg_rera_extractor.api.app:app --reload`

Key endpoints:
- `GET /health` – readiness probe (returns `{"status": "ok"}`).
- `GET /projects?district=...&status=...&limit=20` – list projects with filters and pagination.
- `GET /projects/{state_code}/{rera_registration_number}` – detailed project payload.

Example checks:
- `curl "http://127.0.0.1:8000/health"`
- `curl "http://127.0.0.1:8000/projects?limit=5"`

Confirm the server logs show startup without errors, and responses include project data once the DB is populated.

## 8. Feature Checklist – “What is working?”

| Area               | Check command / action                                          | Working? |
|--------------------|----------------------------------------------------------------|----------|
| Self-check         | `python tools/self_check.py`                                   | [ ]      |
| DRY_RUN crawl      | Run DRY_RUN and see expected combinations                      | [ ]      |
| FULL small crawl   | Run FULL with small config, see V1 JSON + run_report populated | [ ]      |
| DB init            | `python tools/init_db.py` completes without error              | [ ]      |
| DB load            | `python tools/load_runs_to_db.py --run-id <id>`                | [ ]      |
| API /health        | `curl /health` returns status=ok                               | [ ]      |
| API /projects      | `curl /projects?limit=5` returns a small list of projects      | [ ]      |

## 9. Optional: Jira integration (short admin note)
Jira sync tooling exists for repo maintainers (`tools/sync_dev_plan_to_jira.py` and the GitHub Actions workflow). Regular users running crawls/DB/API can ignore Jira configuration; no Jira settings are needed for the steps above.
