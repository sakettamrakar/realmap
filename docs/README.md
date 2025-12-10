# CG RERA Real Estate Intelligence Platform

This documentation describes the CG RERA scraper, data pipeline, geo/amenity enrichment, and API/UX layers that power a compliant real estate intelligence platform for Chhattisgarh.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Data Pipeline](#data-pipeline)
- [Scraper Engine](#scraper-engine)
- [Geo Intelligence](#geo-intelligence)
- [Amenities Engine](#amenities-engine)
- [UI & UX](#ui--ux)
- [Deployment](#deployment)
- [Debug & Runbook](#debug--runbook)
- [API Reference](#api-reference)
- [Changelog](#changelog)
- [Glossary](#glossary)
- [Contributing](#contributing)

## Overview

This project ingests RERA-registered projects from the CG RERA portal, normalizes them into a structured data model, enriches them with geo and amenity context, and exposes them via a FastAPI backend and React/Vite frontend.

- Backend: Python, FastAPI, SQLAlchemy, PostgreSQL
- Scraper: Playwright-based browser automation with manual CAPTCHA support
- Data: Projects, promoters, buildings, units, bank accounts, land parcels, documents, artifacts
- Enrichment: Geocoding, amenities, project scores
- UI: Map + list explorer, detail pages, QA tools

### Quick Start

1. Install dependencies and set up the database (see `Deployment-Guide.md`).
2. Run a small debug crawl with QA and DB load:

```bash
python tools/dev_fresh_run_and_qa.py --mode full --config config.debug.yaml
python tools/load_latest_run_into_db.py --config config.debug.yaml
```

3. Start the API and frontend:

```bash
python -m cg_rera_extractor.api.main
cd frontend
npm run dev
```

4. Open the frontend (default http://localhost:5173) and explore projects.

## Architecture

See `Architecture.md` for high-level system design, components, and sequence diagrams.

## Data Pipeline

See `Data-Pipeline.md` for ingestion, loaders, geocoding, and amenity enrichment.

## Scraper Engine

See `Scraper-Engine.md` for Playwright flows, run modes, and configuration.

## Geo Intelligence

See `Geo-Intelligence.md` for address normalization, geocoding providers, and QA.

## Amenities Engine

See `Amenities-Engine.md` for POI providers, amenity stats, and scoring.

## UI & UX

See `UI-UX-Design.md` for screens, flows, and frontend architecture.

## Deployment

See `Deployment-Guide.md` for local and production deployment instructions.

## Debug & Runbook

See `Debug-Runbook.md` for operational runbooks and failure-handling guides.

## API Reference

See `API-Reference.md` for endpoints and payloads.

## Changelog

See `Changelog.md` for major changes and release notes.

## Glossary

See `Glossary.md` for domain and system terminology.

## Contributing

- Follow the coding style and testing guidelines in `DEV_GUIDE.md`.
- Open small, focused pull requests with tests.
- Keep documentation updated when changing core flows (scraper, pipeline, API, or UI).
