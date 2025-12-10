# Architecture Summary

At a high level, the system flows from the CG RERA portal to scraping and normalization, then through enrichment pipelines into a PostgreSQL database, and finally out through a FastAPI API and React/Vite frontend.

```mermaid
flowchart LR
  A[CG RERA Portal] --> B[Scraper Engine (Playwright)]
  B --> C[Runs: HTML + V1 JSON]
  C --> D[DB Loader]
  D --> E[PostgreSQL]
  E --> F[Geo Pipeline]
  E --> G[Amenities & Scores]
  E --> H[Discovery & Trust]
  E --> I[Read Model / Views]
  I --> J[FastAPI]
  J --> K[React/Vite Frontend]
```

## Major Components

- **Scraper Engine** (`cg_rera_extractor/browser`, `listing`, `detail`, `parsing`, `outputs`)
  - Playwright sessions and selectors drive listing + detail crawls.
  - Output is organized into per-run directories with listings, raw HTML, normalized V1 JSON, logs, and QA artifacts.
- **Loader & Database** (`cg_rera_extractor/db`)
  - SQLAlchemy models for projects, promoters, buildings, unit types, bank accounts, land parcels, artifacts, locations, amenity stats, scores, tags, verification, and landmarks.
  - Loader scripts convert V1 JSON into upsert operations and maintain raw JSON for audit.
- **Geo Pipeline** (`cg_rera_extractor/geo`, geo tools in `tools/`)
  - Normalizes addresses and geocodes projects using configurable providers.
  - Uses a SQLite cache and dedicated QA tooling to validate coverage.
- **Amenities & Scoring** (`cg_rera_extractor/amenities` and related tools)
  - Fetches amenity POIs, aggregates project-level stats, and computes project scores.
- **Discovery & Trust** (`cg_rera_extractor/db/models_discovery.py`, `cg_rera_extractor/api/services/discovery.py`)
  - Manages locality tags, RERA verification records, and curated landmarks.
- **API Layer** (`cg_rera_extractor/api`)
  - FastAPI app with routers for projects, discovery, and tags.
  - Read model and service layer for search, map, detail, and export endpoints.
  - Rate limiting and ops middleware wrap the external surface.
- **Frontend** (`frontend/`)
  - React/Vite SPA for map/list and project detail views.
  - Shared components for scores, discovery badges, mobile navigation, and compliance flows.

## Data Flow

1. **Scrape**: A run is executed via CLI, writing `listings/`, `raw_html/`, `scraped_json/`, and logs under a timestamped `runs/` directory.
2. **Load**: Loader scripts read V1 JSON and upsert normalized data into Postgres, capturing provenance and QA flags.
3. **Enrich**: Geo and amenity pipelines operate on projects to populate coordinates, amenity stats, and scores.
4. **Read Model**: A Phase 6 read model (views/indexes) combines core tables into search-friendly projections.
5. **Serve**: FastAPI exposes search/map/detail endpoints backed by the read model.
6. **Render**: The frontend uses these endpoints to power filters, maps, detail panels, and mobile flows.

For implementation-level details, see `../03-engineering/system-architecture.md`. For schema and table descriptions, see `../03-engineering/data-models.md`. 