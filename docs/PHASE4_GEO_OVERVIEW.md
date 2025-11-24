# Phase 4 GEO Overview

This guide explains how Phase 4 GEO wiring works end-to-end: normalizing project addresses, geocoding them with a configurable provider, persisting results to the database, and validating quality. It is intended for operators running the pipeline and developers debugging it.

## Purpose

Phase 4 adds a reproducible geocoding pipeline so that every project record has:
- A normalized, geocoder-ready address string.
- Latitude/longitude plus provider metadata (`geo_precision`, `geo_source`, `geocoding_status`, `formatted_address`).
- QA checks to surface coverage and obvious errors.

## Data flow at a glance

1. **Extracted project**: Projects loaded into the DB from V1 JSON runs already contain structured address fields (`full_address`, `district`, `tehsil`, optional `pincode`, etc.).
2. **Normalize address**: `tools/backfill_normalized_addresses.py` assembles a canonical `normalized_address` using the Phase 4 rules (ordered components, cleaned punctuation, state expansion, and low-confidence flagging).【F:docs/PHASE4_GEO_DESIGN.md†L5-L64】【F:tools/backfill_normalized_addresses.py†L20-L77】
3. **Geocode**: `tools/geocode_projects.py` finds projects missing coordinates and calls the configured geocoder (with caching) to set `latitude`, `longitude`, `geo_precision`, `geo_source`, `geocoding_status`, and `formatted_address`.【F:docs/GEO_PIPELINE.md†L1-L63】【F:tools/geocode_projects.py†L15-L77】
4. **Persist**: Successful lookups commit updates to the `projects` table; failures set `geocoding_status=FAILED` for visibility.【F:tools/geocode_projects.py†L52-L82】
5. **QA**: `tools/check_geo_quality.py` evaluates coverage, bounding-box sanity, missing normalized addresses, and geocoding status distribution, with samples for manual review.【F:docs/GEO_QA_PLAN.md†L1-L32】【F:tools/check_geo_quality.py†L1-L112】

## Runbook

### 1) Ensure schema is migrated

Run the standard database initialization and migrations before touching GEO data:

```bash
python tools/init_db.py
python tools/run_migrations.py
```

Use `python tools/check_db_counts.py` if you want to verify the database target and confirm GEO columns exist (reports appear in the counts output).【F:docs/DB_GUIDE.md†L1-L52】

### 2) Backfill normalized addresses

Populate `normalized_address` for legacy rows or newly ingested runs:

```bash
# Dry run to inspect outputs
python tools/backfill_normalized_addresses.py --config config.example.yaml --limit 100 --dry-run

# Commit updates (remove --dry-run and optional limit)
python tools/backfill_normalized_addresses.py --config config.example.yaml
```

Notes:
- The script targets rows where `normalized_address` is `NULL`/empty and logs skipped cases when no usable components exist.
- Low-confidence strings (e.g., missing district) are counted but still written so geocoding can proceed or be reviewed.【F:tools/backfill_normalized_addresses.py†L57-L99】

### 3) Geocode projects

Run geocoding for projects lacking coordinates or provider metadata:

```bash
# Use config for DB + geocoder; geocode up to 100 projects (default limit)
python tools/geocode_projects.py --config ./config.example.yaml

# Override provider and limit explicitly
python tools/geocode_projects.py --provider nominatim --limit 25

# Dry run to test provider responses without committing
python tools/geocode_projects.py --dry-run --limit 10
```

Behavior highlights:
- Selects projects with a `normalized_address` where any of `latitude`, `longitude`, or `geo_source` is missing.
- Applies caching and provider throttling per `geocoder` config; successes set coordinates and metadata, failures mark `geocoding_status=FAILED` and continue.【F:docs/GEO_PIPELINE.md†L27-L63】【F:tools/geocode_projects.py†L41-L82】

### 4) Run GEO QA

Validate outputs after a batch:

```bash
python tools/check_geo_quality.py --output-json runs/geo_qa_report.json --sample-size 5
```

What you get:
- Console summary of coverage, missing lat/lon counts, out-of-bounds coordinates, and missing normalized addresses, plus geocoding status distribution.
- Optional JSON report (disable with `--no-write`).【F:tools/check_geo_quality.py†L118-L165】【F:docs/GEO_QA_PLAN.md†L1-L32】

## Provider configuration and rate limits

- Providers are configured under `geocoder` in the YAML config; supported values are `nominatim` (default) and `google` (`geocoder.provider`).【F:docs/GEO_PIPELINE.md†L7-L36】
- Set `geocoder.api_key` for Google; **never commit keys**. Environment injection or a local config file is preferred.
- Respect rate limits and cost: use `geocoder.rate_limit_per_sec`, `request_timeout_sec`, and retry/backoff settings to throttle requests. Lower values reduce provider cost/risk; the SQLite cache (`geocoder.cache_path`) prevents repeat charges on identical addresses.【F:docs/GEO_PIPELINE.md†L7-L38】【F:docs/GEO_PIPELINE.md†L41-L54】
- To switch providers for a run, either change the config or pass `--provider` to `tools/geocode_projects.py` (overrides config).【F:tools/geocode_projects.py†L20-L36】

## Troubleshooting

- **No GEO columns after migration**: Re-run `tools/run_migrations.py` and confirm you are pointing at the correct DB via `DATABASE_URL` or config; `tools/check_db_counts.py` echoes the target.【F:docs/DB_GUIDE.md†L1-L52】
- **Normalized address missing/blank**: Inspect the source fields for the project (address line, district, tehsil, state code). Use `--dry-run --limit` to sample and confirm the normalization logic before committing.【F:tools/backfill_normalized_addresses.py†L57-L99】
- **Provider failures or timeouts**: Lower `rate_limit_per_sec`, increase `request_timeout_sec`, and re-run with a smaller `--limit`. Check logs for `Geocoding failed` messages to identify problematic records.【F:docs/GEO_PIPELINE.md†L7-L38】【F:tools/geocode_projects.py†L58-L82】
- **Coordinates look wrong or outside India**: Run `tools/check_geo_quality.py` to surface out-of-bounds samples. If a provider is consistently off, try switching providers or adjusting normalized address quality (e.g., ensure district is present).【F:tools/check_geo_quality.py†L1-L112】
- **Cache unexpectedly stale**: Delete the cache file (default `data/geocode_cache.sqlite`) to force fresh provider calls; be mindful of rate limits and cost when doing so.【F:docs/GEO_PIPELINE.md†L41-L54】

