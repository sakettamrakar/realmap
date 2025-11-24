# DB Guide

Tools for initializing, loading, and verifying the CG RERA database. Postgres is assumed; `DATABASE_URL` or `db.url` in your config controls the target.

## Core commands

1) Initialize schema (run once per database):
```
python tools/init_db.py
```

2) Apply non-destructive migrations (idempotent; safe to re-run):
```
python tools/run_migrations.py
```

3) Load run outputs (V1 JSON from `scraped_json/`):
```
# Latest run under default outputs/runs
python tools/load_runs_to_db.py --latest

# Specific run id or custom runs dir
python tools/load_runs_to_db.py --run-id run_20251117_123456
python tools/load_runs_to_db.py --runs-dir ./outputs/demo-run/runs --latest
```

4) Verify counts or inspect a project (also reports GEO schema presence):
```
python tools/check_db_counts.py
python tools/check_db_counts.py --project-reg CG-REG-001 --state-code CG
```

`tools/system_full_check.py` chains a crawl and DB verification if you want a supervised end-to-end pass.

## Schema overview

Tables: `projects`, `promoters`, `buildings`, `unit_types`, `project_documents`, `quarterly_updates` (and related metadata tables used by loaders/tests). Natural key is `state_code + rera_registration_number`.

GEO columns defined in `docs/PHASE4_GEO_DESIGN.md` (precision, confidence, source, and normalized/formatted addresses) are added to the `projects` table via the migration step above.

## Troubleshooting

- Counts are zero: ensure the run directory contains `.v1.json` files under `scraped_json/`, confirm `DATABASE_URL` points to the expected instance, and re-run `init_db.py`.
- Loader errors on missing fields: inspect the offending JSON and adjust mappings; rerun the load.
- Wrong database target: print the resolved target via `python tools/check_db_counts.py --help` (the tools echo the database) and correct `DATABASE_URL` or config.

## API reminder

After loading data, start the API for read-only queries:
```
uvicorn cg_rera_extractor.api.app:app --reload
```
Use `/health` for readiness and `/projects` or `/projects/{state_code}/{registration_number}` for data.
