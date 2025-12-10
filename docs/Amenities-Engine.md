# Amenities Engine

This document summarizes the amenity enrichment and scoring pipeline.

For design details, see:

- `PHASE5_AMENITY_DESIGN.md`
- `PHASE5_AMENITY_OVERVIEW.md`
- `AMENITY_PROVIDER.md`
- `AMENITY_STATS.md`
- `PROJECT_SCORES.md`

## Goals

- Use project coordinates to fetch nearby points of interest (POIs).
- Aggregate POIs into amenity stats per project, amenity type, and radius.
- Compute composite scores (location, amenity, overall, lifestyle, etc.).

## Key Tables

- `AmenityPOI`: cached POI records from an external provider.
- `ProjectAmenityStats`: aggregated amenity stats per project and radius.
- `ProjectScores`: composite project scores.

## Commands

```bash
# Fetch amenity POIs (sample)
python tools/fetch_amenities_sample.py --config config.phase2.sample.yaml --limit 10

# Compute amenity stats
python tools/compute_project_amenity_stats.py --config config.phase2.sample.yaml --limit 50

# Compute project scores
python tools/compute_project_scores.py --limit 50

# Run amenity & score QA
python tools/check_amenity_and_scores_quality.py --output-json runs/amenity_qa_report.json
```

See `PHASE5_AMENITY_OVERVIEW.md` for the complete end-to-end description.
