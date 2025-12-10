# Code Structure

This document summarizes how the codebase is organized and how to orient yourself as a developer.

## Backend modules

Under `cg_rera_extractor/`:

- `browser/` – Playwright browser/session wrappers and manual CAPTCHA handling.
- `config/` – Dataclasses or Pydantic models describing config schemas.
- `listing/` – Search-page interactions, pagination, and listing-level extraction.
- `detail/` – Detail page navigation, HTML capture, and optional preview capture.
- `parsing/` – Parsers that translate HTML into structured fields and V1 JSON.
- `outputs/` – Helpers for file naming and run directory layouts.
- `qa/` – Field-by-field QA helpers and comparison utilities.
- `db/` – SQLAlchemy models, loader methods, migrations, and DB helper functions.
- `geo/` – Geocoding helpers and address normalization logic.
- `amenities/` – Amenity POI, stats, and scoring utilities.
- `api/` – FastAPI app (`app.py`), routers, schemas, dependencies, services, and middleware.

`tools/` holds top-level CLI scripts for common workflows (crawl+QA, DB init/load, geo, amenities, system checks).

## Development workflows

Recommended entrypoints:

- Quick health checks:
  - `python tools/self_check.py`
  - `python tools/system_full_check.py`
- Dev smoke for crawl + QA:
  - `python tools/dev_fresh_run_and_qa.py --mode full --config config.debug.yaml`
- DB checks:
  - `python tools/check_db_counts.py`

Tests are under `tests/` and cover parsing, QA, DB loaders, geo/amenity tools, and API behavior.

## Frontend structure

Under `frontend/src/`:

- `components/` – React components for:
  - Map/list views.
  - Project detail panels (hero, price, amenities, location, intelligence sections).
  - Shared widgets (scores, trust badges, filters, etc.).
  - Mobile navigation and compliance flows.
- `api/` – API client wrappers encapsulating calls to the backend.
- `styles` or CSS modules – styling for components and layout.
- `App.tsx` – top-level app component that wires routing and layout, including mobile vs desktop experiences.

The frontend README and the mobile UX docs provide more context on how components are intended to be used.

## AI collaboration notes

When using AI tools on this repository:

- Keep parsing logic, network code, and DB loaders separated.
- Respect existing run directory structure and config-driven behavior.
- Avoid hard-coding secrets or environment-specific paths.

The root `AI_Instructions.md` contains additional expectations for AI changes.
