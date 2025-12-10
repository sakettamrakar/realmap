# Deployment Guide

This document describes how to run the CG RERA platform locally and in production-like environments.

## Prerequisites

- Python 3.11+
- Node.js (for frontend)
- PostgreSQL (recommended for production; SQLite possible for local testing)
- Playwright browsers installed (`python -m playwright install`)

## Local Development

1. Install Python dependencies:

```bash
pip install -e .
``` 

2. Initialize the database:

```bash
python tools/init_db.py
python tools/run_migrations.py
```

3. Run a small crawl and load it into the DB:

```bash
python tools/dev_fresh_run_and_qa.py --mode full --config config.debug.yaml
python tools/load_latest_run_into_db.py --config config.debug.yaml
```

4. Start the API:

```bash
python -m cg_rera_extractor.api.main
```

5. Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

## Production Considerations

- Run API and frontend in containers or managed services.
- Use a managed PostgreSQL instance.
- Configure geocoding and amenity providers with appropriate API keys.
- Schedule batch jobs for crawl, DB load, geo, amenities, and scores (e.g., cron or Airflow).
- Centralize logs and metrics for API and batch jobs.

## Configuration

- Base config examples:
  - `config.example.yaml`: full pipeline demo.
  - `config.debug.yaml`: small debug run.
  - `config.phase2.sample.yaml`: safe listing-only crawl.

See `Debug-Runbook.md` for operational troubleshooting.
