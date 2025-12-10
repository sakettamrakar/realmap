# Deployment Guide

This guide covers running the platform locally and outlines considerations for staging/production-like environments.

## Local development

1. Set up Python and Postgres as described in `../01-getting-started/installation-setup.md`.
2. Copy or create a config file (e.g., `config.debug.yaml`).
3. Initialize the database and apply migrations:

```powershell
python tools/init_db.py
python tools/run_migrations.py
```

4. Run a small crawl and load it into the DB:

```powershell
python tools/dev_fresh_run_and_qa.py --mode full --config config.debug.yaml
python tools/load_runs_to_db.py --latest
```

5. Start the API:

```powershell
python -m cg_rera_extractor.api.main
```

6. Start the frontend in `frontend/`:

```powershell
cd frontend
npm install
npm run dev
```

## Staging / production-like environments

For a more durable deployment:

- Run the API and frontend in containers or managed services.
- Use a managed Postgres instance.
- Configure geocoding and amenity providers via environment variables or secret managers.
- Schedule batch jobs (cron, Airflow, etc.) for crawl, load, geo, amenities, and scoring phases.
- Centralize logs and metrics for the API and batch jobs.

The exact setup depends on your infrastructure, but the separation between batch pipelines and the read-only API makes it straightforward to schedule enrichment separately from serving.
