# Geo Intelligence

This document summarizes the geocoding and geo-quality pipeline.

For detailed design and runbooks, see:

- `GEO_PIPELINE.md`
- `PHASE4_GEO_OVERVIEW.md`
- `GEO_QA_PLAN.md`

## Goals

- Normalize project addresses into a canonical `normalized_address`.
- Geocode projects with a configurable provider (Nominatim or Google).
- Cache responses to avoid duplicate calls.
- Persist coordinates and metadata in the database.
- Provide QA tools to validate coverage and sanity.

## Key Tables

- `projects`: stores `normalized_address`, `latitude`, `longitude`, `geo_precision`, `geo_source`, `geocoding_status`, `geo_formatted_address`.
- `AmenityPOI`: cached POI locations (used by amenities phase).
- `ProjectLocation`: candidate locations per project, per source.

## Commands

- Backfill normalized addresses:

```bash
python tools/backfill_normalized_addresses.py --config config.example.yaml --limit 100 --dry-run
python tools/backfill_normalized_addresses.py --config config.example.yaml
```

- Geocode projects:

```bash
python tools/geocode_projects.py --config ./config.example.yaml --limit 50
python tools/geocode_projects.py --provider nominatim --limit 10
```

- Run geo QA:

```bash
python tools/check_geo_quality.py --output-json runs/geo_qa_report.json --sample-size 5
```

See `GEO_PIPELINE.md` and `PHASE4_GEO_OVERVIEW.md` for provider configuration, caching, and troubleshooting.
