# Environment & Configuration

This document explains how configuration is organized and how environments are wired.

## 1. Configuration files

Core configuration lives in YAML files at the repo root:

- `config.example.yaml` – full demo configuration, including scraper, DB, geo, and amenity sections.
- `config.debug.yaml` – conservative, small-scope config for local development and QA.
- `config.phase2.sample.yaml` – safe listing-only crawl used in examples and tests.

Typical top-level sections include:

- `run.*` – run mode, output base directory, concurrency limits.
- `browser.*` – Playwright options (headless, timeouts).
- `search_page.*` – selectors and search defaults for the CG RERA portal.
- `db.*` – database URL and options (if not using `DATABASE_URL`).
- `geocoder.*` – provider, rate limits, cache location.
- `amenities.*` – provider credentials and query limits.

## 2. Environment variables

Recommended environment variables:

- `DATABASE_URL` – SQLAlchemy-style Postgres URL.
- Provider-specific keys (examples):
  - `NOMINATIM_URL` or equivalent override, when using a self-hosted geocoder.
  - `GOOGLE_GEOCODING_API_KEY` (if configured in your YAML).
  - Amenity/POI provider API keys.

On Windows PowerShell:

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://user:password@localhost/realmap_dev"
```

## 3. Run modes

The scraper supports multiple modes (see `cg_rera_extractor/cli.py` and `docs/Scraper-Engine.md`):

- `dry-run` – validate config and search combinations without network or browser.
- `listings-only` – crawl listing pages and JSON without detail HTML.
- `full` – full flow with detail HTML and V1 mapping (manual CAPTCHA required).

Configured in YAML under `run.mode` or on the CLI via `--mode`.

## 4. Environments

Common environment patterns:

- **Local development**
  - SQLite or Postgres on localhost.
  - `browser.headless=false` for debugging selectors and CAPTCHAs.
  - `config.debug.yaml` as a baseline.
- **Staging / sandbox**
  - Managed Postgres.
  - Regular scheduled runs (crawl + load + geo + amenities).
  - More conservative provider rate limits.
- **Production-style**
  - Containerized API + frontend.
  - Externalized secrets via env vars or secret manager.
  - Centralized logging and metrics.

## 5. Safety and compliance

- Do not commit API keys or secrets.
- Respect provider rate limits configured in `geocoder` and amenity sections.
- Keep run output paths and DB URLs environment-specific; avoid pointing development configs at production databases.
