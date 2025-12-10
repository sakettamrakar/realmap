# Data Models

This document summarizes the main database and logical models used across scraping, enrichment, and API layers.

## V1 JSON

The scraper produces a V1 JSON document per project with top-level sections such as:

- `metadata` – schema version and state code.
- `project_details` – core project fields (name, type, status, district, tehsil, address).
- `promoter_details` – list of promoters and contact/ID fields.
- `land_details`, `building_details`, `unit_types`, `bank_details`, `documents`, `quarterly_updates` – structured lists, some of which may be sparsely populated.
- `raw_data` – normalized and unmapped sections from the HTML.
- `previews` – metadata for preview-only artifacts.

The loader is responsible for mapping these sections into normalized relational tables.

## Core tables

At a high level, the relational model includes:

- `projects` – central entity identified by `state_code` and `rera_registration_number`, with key RERA fields, geo fields (normalized address, latitude/longitude, precision, source), QA flags, and raw JSON payload for audit.
- `promoters` – project promoters linked to projects.
- `buildings`, `unit_types` – towers/blocks and unit configurations.
- `bank_accounts` – designated RERA bank accounts linked to projects.
- `land_parcels` – land details (survey numbers, areas, encumbrance notes).
- `project_artifacts` – documents and media assets associated with projects (paths, types, formats, and source URLs).
- `quarterly_updates` – periodic project status updates.

## Geo-related tables

Geo enrichment relies on:

- Columns on `projects` for normalized address and primary coordinates.
- Supporting tables and/or views for candidate locations and, where applicable, active location records.

These are populated by scripts like `backfill_normalized_addresses.py` and `geocode_projects.py`.

## Amenity and scoring tables

Amenity and scoring phases introduce:

- POI tables (amenity points of interest) representing schools, hospitals, transit, and other categories.
- `project_amenity_stats` (or similarly named tables) aggregating amenity counts, distances, and category slices per project and radius.
- `project_scores` capturing scores along multiple dimensions (location, amenity, safety, etc.), plus versions and timestamps.

The scoring logic is implemented in dedicated tools and keeps scores auditable via raw stats and versioning metadata.

## Discovery and trust tables

To support discovery and trust features:

- Tag tables and project-tag join tables encode locality/investment tags and their application to projects.
- Verification tables track RERA verification status, official record URLs, current flags, and timestamps.
- Landmark tables and project-landmark join tables associate projects with curated points of interest.

These structures are consumed by API services in `api/services/discovery.py`.

## Read model

The Phase 6 read model introduces views that combine commonly queried fields:

- A project search view joining projects, scores, amenity stats, and geo data for search and map endpoints.
- Supporting indexes on administrative fields, scores, and coordinates to keep queries fast.

For more detail, consult migration scripts and model definitions in `cg_rera_extractor/db` alongside the historical `PHASE6_READ_MODEL.md` document. Operational usage of the schema is described in `../04-operations/devops-pipeline.md`.
