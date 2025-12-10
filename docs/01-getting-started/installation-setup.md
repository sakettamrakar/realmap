# Installation & Setup

This document covers installing dependencies and preparing environments for local development.

## 1. Python environment

From the repo root on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

To work on the package in editable mode:

```powershell
pip install -e .
```

## 2. PostgreSQL

You can run against a local Postgres instance or a remote one.

- Create a database (e.g., `realmap_dev`).
- Set `DATABASE_URL` in your shell, or configure `db.url` in your YAML config:

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://user:password@localhost/realmap_dev"
```

Initialize schema and apply migrations:

```powershell
python tools/init_db.py
python tools/run_migrations.py
```

Use `python tools/check_db_counts.py` to confirm connectivity and table presence.

## 3. Node.js and frontend

In the `frontend/` directory:

```powershell
cd frontend
npm install
```

The frontend reads `VITE_API_BASE_URL` from `.env`:

```bash
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
```

Copy from the example if needed:

```powershell
cd frontend
copy .env.example .env
```

## 4. Configuration files

Several YAML configs define scraper and pipeline behavior:

- `config.example.yaml` – full pipeline demo.
- `config.debug.yaml` – small debug run appropriate for local development.
- `config.phase2.sample.yaml` – safe LISTINGS_ONLY run.

Key fields:

- `run.mode`: `dry-run`, `listings-only`, or `full`.
- `run.output_base_dir`: base directory for run artifacts.
- `browser.headless`: `true`/`false`.
- `db.url`: database URL (if not using `DATABASE_URL`).
- `search_page.selectors.*`: selectors for the RERA search page.

For environment-specific secrets (e.g., geocoder or amenity provider keys), prefer environment variables or local configs ignored by git.
