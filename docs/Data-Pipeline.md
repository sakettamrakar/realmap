# Data Pipeline

> **Last Updated**: December 10, 2024 (Data Audit Implementation)

This document describes how raw CG RERA pages become enriched, queryable project records.

## Stages

1. **Scraping**: Playwright-based crawler collects listing and detail HTML and normalizes them into V1 JSON.
2. **Parsing**: Raw HTML is parsed into sections and fields, then mapped to V1 schema with key variant matching.
3. **Loading**: Loader scripts upsert V1 JSON into PostgreSQL with QA validation and provenance tracking.
4. **Geo Enrichment**: Address normalization and geocoding to produce canonical coordinates and metadata.
5. **Amenity Enrichment**: Amenity provider lookups, stats aggregation, and scoring.
6. **API Read Model**: Optimized views for search/map/detail endpoints.

## Parsing Pipeline

### Files
- `cg_rera_extractor/parsing/raw_extractor.py` - HTML to raw sections
- `cg_rera_extractor/parsing/mapper.py` - Raw sections to V1 schema
- `cg_rera_extractor/parsing/data/logical_sections_and_keys.json` - Key variants configuration

### Key Features (2024-12-10 Enhancements)

| Feature | Implementation |
|---------|----------------|
| Date Parsing | `_normalize_date()` handles 7 date formats (DD/MM/YYYY, DD-MM-YYYY, etc.) |
| Pincode Extraction | `_extract_pincode()` extracts 6-digit pincodes from address strings |
| Document Classification | `_infer_doc_type()` categorizes documents by field key patterns |
| Key Variant Matching | 400+ key variants across 8 sections for improved field extraction |

### Configuration: `logical_sections_and_keys.json`

Sections supported:
- `project_details` - 18 fields with ~80 key variants
- `promoter_details` - 10 fields with ~60 key variants
- `land_details` - 8 fields with ~40 key variants
- `building_details` - 10 fields with ~35 key variants
- `unit_types` - 8 fields with ~30 key variants
- `bank_details` - 6 fields with ~20 key variants
- `documents` - 4 fields with ~15 key variants
- `quarterly_updates` - 10 fields with ~30 key variants

## Ingestion & Loader

- Input: `runs/run_<id>/scraped_json/*.v1.json` produced by the scraper.
- Loader: `cg_rera_extractor.db.loader.load_run_into_db` reads each file and upserts:
  - `Project`, `Promoter`, `Building`, `UnitType`, `ProjectDocument`, `QuarterlyUpdate`, `BankAccount`, `LandParcel`, `ProjectArtifact`, `ProjectLocation`.
- Raw payloads are stored in `projects.raw_data_json` for audit and re-processing.

### Loader Enhancements (2024-12-10)

| Enhancement | Description |
|-------------|-------------|
| `scraped_at` Population | Set from metadata or current timestamp |
| Provenance Tracking | `data_provenance` records created for each project |
| QA Validation | `qa_flags`, `qa_status`, `qa_last_checked_at` populated |
| Extra Fields | `pincode`, `village_or_locality`, `project_website_url` extracted |
| Land Parcels | Now properly loaded from `v1_project.land_details` |
| Artifact URLs | Relative URLs resolved to absolute paths |
| Artifact Categories | Inferred from field key (legal, technical, approvals, media) |

### Commands

```bash
# Load a specific run directory
python tools/load_run_into_db.py --run-dir outputs/realcrawl/run_2025XXXX

# Load all runs under a base directory
python tools/load_all_runs_into_db.py --base-dir outputs/realcrawl

# Run database migrations
python migrations/run_migration.py
```

See `DB_GUIDE.md` and `DATA_MODEL_TARGET.md` for full schema and loader behavior.

## Data Normalization Utilities

### File: `cg_rera_extractor/utils/normalize.py`

Provides standardized normalization functions:

| Category | Functions |
|----------|-----------|
| Area | `normalize_area_to_sqm()`, `normalize_area_to_sqft()`, `sqm_to_sqft()`, `sqft_to_sqm()` |
| Price | `normalize_price()`, `price_per_sqft()`, `format_price_lakhs()` |
| Categories | `normalize_project_status()`, `normalize_project_type()` |
| Text | `normalize_whitespace()`, `normalize_name()`, `extract_numeric()` |

Features:
- Handles Indian number formats (lakhs, crores, ₹ symbol)
- Supports multiple area units (sqft, sqm, acres, hectares)
- Normalizes project statuses/types to canonical values

## Geocoding Pipeline

Geocoding is handled by tools in `cg_rera_extractor/geo` and documented in `GEO_PIPELINE.md` and `PHASE4_GEO_OVERVIEW.md`.

High-level flow:

1. Backfill `normalized_address` using `tools/backfill_normalized_addresses.py`.
2. Geocode projects with `tools/geocode_projects.py` using Nominatim or Google.
3. Cache responses in SQLite to avoid repeated provider calls.
4. Run `tools/check_geo_quality.py` to validate coverage and spot anomalies.

## Amenity & Scoring Pipeline

Amenity and scoring phases are documented in `PHASE5_AMENITY_OVERVIEW.md`, `AMENITY_PROVIDER.md`, `AMENITY_STATS.md`, and `PROJECT_SCORES.md`.

Flow:

1. Fetch amenity POIs near project coordinates.
2. Aggregate POIs into slices per project, amenity type, and radius.
3. Compute composite scores (`project_scores`) from amenity stats and weights.
4. Run QA via `tools/check_amenity_and_scores_quality.py`.

## QA Integration

QA is performed at multiple stages:

- **Loading**: QA validation gate checks for price outliers, missing fields, bounds exceeded.
- **Field-by-field**: Comparison between HTML and V1 JSON (`QA_GUIDE.md`).
- **Geo quality**: Coordinate validation and precision checks (`GEO_QA_PLAN.md`).
- **Amenity and score**: Distribution and outlier checks (`PHASE5_AMENITY_OVERVIEW.md`).

### Data Quality Tools

```bash
# Check scoring coverage
python tools/check_scoring_coverage.py

# Check geo quality
python tools/check_geo_quality.py

# Data audit query
python tools/data_audit_query.py
```

## Read Model & API

Phase 6 defines a read model and API surface (`PHASE6_READ_MODEL.md`, `PHASE6_API_DESIGN.md`):

- Materialized views or join queries combining `projects`, `project_scores`, and `project_amenity_stats`.
- FastAPI routes implement `/projects/search`, `/projects/map`, and `/projects/{id}`.

See `API-Reference.md` for concrete endpoint and payload details.

## Database Migrations

Migration files are stored in `/migrations/`:

| File | Description |
|------|-------------|
| `V001_data_audit_schema_upgrade.sql` | Data audit schema changes (48 new columns) |
| `run_migration.py` | Python migration runner |

Run migrations:
```bash
python migrations/run_migration.py
```
