# CG RERA Extraction Framework

This repository hosts the extraction (E) layer for the Chhattisgarh (CG) RERA data
pipeline. The framework focuses on collecting data from the official CG RERA
portal and producing a normalized **V1 scraper JSON** output. Transformation and
loading steps happen in downstream repositories.

## Repository layout

```
cg_rera_extractor/
  browser/      # Browser/session management abstractions
  config/       # Config models and loaders
  detail/       # Detail page fetchers
  listing/      # Listing page scrapers and models
  outputs/      # Helpers for writing run artefacts
  parsing/      # HTML -> JSON parsing utilities
  runs/         # Run metadata and orchestrator
```

Additional documentation:

- [`AI_Instructions.md`](./AI_Instructions.md)
- [`DEV_PLAN.md`](./DEV_PLAN.md)

## Configuration

Configuration lives in YAML files that follow the schema documented in
`cg_rera_extractor.config`. Use [`config.example.yaml`](./config.example.yaml) as
a reference when creating your own configuration. Load the configuration within
Python code using `cg_rera_extractor.config.load_config`.

## Tests

We use `pytest` for testing. All parsing logic and orchestrator components must
be covered by unit tests using saved HTML fixtures, allowing test execution
without hitting the live CG RERA portal.

## API service

A lightweight FastAPI app exposes read-only endpoints for project summaries and
details backed by the normalized Postgres database. To run it locally, set a
`DATABASE_URL` and start uvicorn:

```bash
export DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/cg_rera
uvicorn cg_rera_extractor.api.app:app --reload
```
