# Product Overview

This platform ingests Chhattisgarh RERA (CG RERA) project data, normalizes it into a structured schema, enriches it with geo and amenity intelligence, and exposes it via a FastAPI backend and React/Vite frontend for map + list exploration and analyst workflows.

## Problem

- Regulatory RERA portals expose rich project information but are hard to search, analyze, or compare at scale.
- Project pages mix structured and unstructured content, with inconsistent address formats and preview-only documents.
- Downstream stakeholders (analysts, investors, compliance teams) need trustworthy, queryable data with clear provenance and QA.

## Solution

This repository provides an end-to-end data and application stack:

- **Playwright-based scraper** for CG RERA listing and detail pages.
- **V1 JSON schema** mapping raw HTML into normalized project payloads.
- **Field-by-field QA tools** that compare HTML vs JSON outputs.
- **PostgreSQL-backed loader** that stores projects, promoters, geo fields, amenities, and scores.
- **Geo pipeline** to normalize addresses, geocode projects, and run geo QA.
- **Amenity and scoring pipeline** to fetch nearby POIs, compute amenity stats, and produce project scores.
- **FastAPI service** that exposes read-only endpoints for projects and discovery use cases.
- **React/Vite frontend** for map and detail exploration, including mobile-focused UX.

## Key Capabilities

- **Crawl & Normalize**: Config-driven browser sessions that support DRY_RUN, LISTINGS_ONLY, and FULL modes, writing artifacts per run under a stable directory layout.
- **Reproducible QA**: Deterministic field-by-field QA reports per run (`qa_fields_report.json/md`) for auditing scraper correctness.
- **Rich Data Model**:
  - Projects, promoters, buildings, unit types, bank accounts, land parcels.
  - Geo columns (normalized address, lat/lon, precision, source, status).
  - Amenity POIs, project amenity stats, and project scores.
  - Discovery entities: tags, RERA verification, and landmarks.
- **Provenance & Auditing**:
  - Per-project provenance records for HTML, JSON, and network traces.
  - Per-run ingestion audits with counts, durations, and QA summaries.
- **API Layer**:
  - Health checks and project lookups by state + registration.
  - Search/map endpoints backed by a Phase 6 read model.
  - Discovery endpoints for tags, verification, and landmarks.
- **Frontend UX**:
  - Desktop and mobile layouts for map/list and project detail.
  - Trust badges, filters, and discovery widgets (tags, landmarks).

## Who This Is For

- **Data engineers / developers** building and maintaining the scraper, pipelines, and API.
- **Analysts** needing high-quality project data, geo coverage, and amenity/scores for CG RERA.
- **Product & UX teams** iterating on the map/list and mobile-first experiences.

For a visual architecture summary, see `architecture-summary.md`. For a hands-on path from clone to first run, start with `../01-getting-started/quickstart.md`. 