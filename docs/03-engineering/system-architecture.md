# System Architecture

This document describes the technical architecture of the CG RERA platform, building on the high-level view in `../00-overview/architecture-summary.md`.

## Codebase layout

Key backend modules under `cg_rera_extractor/`:

- `browser/` – Playwright session management and browser utilities (context creation, manual CAPTCHA pause, timeouts).
- `config/` – Config models and helpers for parsing YAML configuration files.
- `listing/` – Search-page navigation, listing pagination, and listing JSON extraction.
- `detail/` – Detail page fetchers and optional preview capture logic.
- `parsing/` – HTML parsing and mapping into the V1 JSON schema.
- `outputs/` – Helpers for naming and writing run artifacts (HTML, JSON, logs, QA).
- `qa/` – Field extraction, comparison logic, and QA helpers used by CLI tools.
- `db/` – SQLAlchemy models, loader utilities, migrations, and ingestion audit/provenance models.
- `geo/` – Address normalization and geocoding helpers.
- `amenities/` – Amenity POI ingestion, project amenity stats, and scoring helpers.
- `api/` – FastAPI application, routers, schemas, services, and middleware (including rate limiting).

The frontend lives under `frontend/` and is a React/Vite app using TypeScript and Leaflet for mapping.

## Scraper engine

The scraper is orchestrated via a CLI entrypoint that wires together browser sessions, listing flows, detail fetchers, and parsers.

- Modes: `dry-run`, `listings-only`, and `full`.
- Configuration is provided by YAML (see `../01-getting-started/environment-config.md`).
- Runs write to a configured base directory under `runs/` or `outputs/`, with a stable layout:
  - `listings/` – listing HTML and extracted JSON.
  - `raw_html/` – detail page HTML snapshots.
  - `scraped_json/` – normalized V1 JSON per project.
  - `logs/` – log files.
  - `qa_fields/` – QA reports (when QA tools have been run).

For more on selectors, run modes, and observability, see `Scraper-Engine.md` (legacy) and `code-structure.md`.

## Loader and database

The loader converts V1 JSON into normalized tables in Postgres:

- Core entities: projects, promoters, buildings, unit types, bank accounts, land parcels, documents/artifacts, quarterly updates.
- Enrichment: geo columns, amenity stats, scores, discovery entities (tags, verification, landmarks).
- Provenance: per-project records noting source HTML, parser version, run IDs, and any extraction warnings.
- Ingestion audits: per-run records with counts, QA summary flags, and basic network ingest metrics.

The loader is used by CLI tools such as `tools/load_runs_to_db.py` and is documented further in `../03-engineering/data-models.md` and `../04-operations/devops-pipeline.md`.

## Geo pipeline

Geo enrichment is handled by utilities in `geo/` and scripts under `tools/`:

- Backfill normalized addresses for projects without a `normalized_address`.
- Geocode projects via a configured provider (Nominatim or Google), using a SQLite cache to avoid duplicate calls.
- Persist coordinates, precision, and provider metadata back into the database.
- Run geo QA to check coverage, bounding boxes, and outliers.

See `../03-engineering/data-models.md` for geo-related tables and `../04-operations/devops-pipeline.md` for runbooks.

## Amenity and scoring pipeline

The amenity pipeline adds:

- Amenity POIs (schools, hospitals, transit, etc.).
- Aggregated project amenity stats for different radii and categories.
- Project scores that summarize location/amenity quality along several dimensions.

These are powered by scripts in `tools/` and models in `amenities` and `db`. Details live in `../03-engineering/data-models.md` and the original amenity engine docs.

## Discovery and trust layer

Discovery and trust augment projects with:

- Tags representing locality and investment signals.
- RERA verification records, status enums, and supporting evidence.
- Landmarks and project-landmark relationships.

Associated routes and services live in `api/services/discovery.py` and `api/routes_discovery.py`. This is described further in `data-models.md` and `api-reference.md`.

## API layer

The API is a FastAPI application that exposes:

- Health and simple project lookup endpoints.
- Search/list and map endpoints operating over the read model.
- Discovery endpoints for tags, verification, and landmarks.

It also includes middleware for rate limiting and basic governance. For endpoint-level details and schemas, see `api-reference.md`.

## Frontend

The frontend is a React/Vite SPA:

- Uses Leaflet to render maps and pins.
- Builds page-level components for map/list, project detail, and supporting widgets.
- Integrates mobile-specific components for navigation and compliance flows.

Frontend internals are described in `code-structure.md` and the original frontend implementation summaries.
