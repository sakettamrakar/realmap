# Architecture

This document describes the end-to-end architecture of the CG RERA Real Estate Intelligence Platform.

## High-Level Overview

```mermaid
flowchart LR
  A[CG RERA Portal] --> B[Scraper Engine]
  B --> C[Raw Artifacts (HTML/JSON)]
  C --> D[Loader & DB]
  D --> E[Geo Pipeline]
  E --> F[Amenities & Scores]
  F --> G[API Layer]
  G --> H[Frontend UI]
  D --> I[QA & Validation]
```

- **Scraper Engine**: Playwright-based crawler that navigates search and detail pages, saving HTML and normalized V1 JSON.
- **Loader & DB**: Upserts normalized runs into PostgreSQL using SQLAlchemy models (`Project`, `Promoter`, `Building`, etc.).
- **Geo Pipeline**: Normalizes addresses, calls geocoding providers, and caches responses with quality checks.
- **Amenities & Scores**: Fetches nearby POIs, aggregates amenity stats, and computes project scores.
- **API Layer**: FastAPI app exposing read-only endpoints for projects, discovery, and analytics.
- **Frontend UI**: Vite/React app for map/list exploration, detail pages, QA dashboards.

## Codebase Layout

- `cg_rera_extractor/browser/`: Playwright session and browser utilities.
- `cg_rera_extractor/listing/`: Listing search, pagination, and parsing.
- `cg_rera_extractor/detail/`: Detail page fetch and preview capture.
- `cg_rera_extractor/parsing/`: HTML parsing and mapping to V1 JSON schema.
- `cg_rera_extractor/quality/`: QA validation and sanity checks.
- `cg_rera_extractor/db/`: SQLAlchemy models, migrations, and loader utilities.
- `cg_rera_extractor/geo/`: Geocoding utilities and normalization helpers.
- `cg_rera_extractor/api/`: FastAPI app, routers, schemas, and services.
- `frontend/`: React app (Vite) for end-user UI.

## Data Flow

1. **Crawl**: Orchestrator runs listing + detail crawls and writes `raw_html/` and `scraped_json/` into `runs/run_<id>/`.
2. **Load to DB**: Loader reads V1 JSON, upserts projects, and attaches raw payloads and artifacts.
3. **Geo Enrichment**: Geo tools backfill `normalized_address` and fetch coordinates.
4. **Amenity Enrichment**: Amenity tools compute POI stats and project scores.
5. **Serve via API**: FastAPI aggregates DB views into search, map, and detail endpoints.
6. **Render UI**: Frontend calls the API to render map, list, and detail experiences.

## Environments

- **Local Development**: SQLite/PostgreSQL via docker, Playwright in headed/CI mode, Vite dev server.
- **Staging/Production**: PostgreSQL, external geocoding provider, containerized services for API and frontend.

See `Data-Pipeline.md`, `Scraper-Engine.md`, and `Geo-Intelligence.md` for deeper dives into each subsystem.
