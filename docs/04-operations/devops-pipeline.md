# DevOps Pipeline

This document describes the operational pipeline from crawling to serving data.

## Stages

1. **Crawl**
   - Run the scraper in `listings-only` or `full` mode.
   - Outputs: listing HTML/JSON, detail HTML (for full), V1 JSON, logs.

2. **QA**
   - Run field-by-field QA tools against a specific run.
   - Outputs: QA reports under `qa_fields/` within the run directory.

3. **Load**
   - Initialize or migrate the database schema.
   - Load the latest or specific runs into Postgres.

4. **Geo enrichment**
   - Backfill normalized addresses for projects missing them.
   - Geocode projects using configured providers and cache results.
   - Run geo QA to validate coverage and detect anomalies.

5. **Amenity and scoring**
   - Fetch amenity POIs near project coordinates.
   - Compute project-level amenity stats and scores.
   - Run QA checks on amenity/score consistency where applicable.

6. **Read model refresh**
   - Refresh views or materialized views used by API search and map endpoints.

7. **Serve**
   - Ensure the API and frontend are pointing at the correct database and environment.

## Example command sequence

```powershell
# 1) Crawl + QA
activate .venv
python tools/dev_fresh_run_and_qa.py --mode full --config config.debug.yaml

# 2) DB init and load
python tools/init_db.py
python tools/run_migrations.py
python tools/load_runs_to_db.py --latest
python tools/check_db_counts.py

# 3) Geo
python tools/backfill_normalized_addresses.py --config config.example.yaml --limit 100 --dry-run
python tools/backfill_normalized_addresses.py --config config.example.yaml
python tools/geocode_projects.py --config config.example.yaml --limit 50
python tools/check_geo_quality.py --output-json runs/geo_qa_report.json --sample-size 5

# 4) Amenities and scores
python tools/fetch_amenities_sample.py --config config.phase2.sample.yaml --limit 10
python tools/compute_project_amenity_stats.py --config config.phase2.sample.yaml --limit 50
python tools/compute_project_scores.py --limit 50
python tools/check_amenity_and_scores_quality.py --output-json runs/amenity_qa_report.json
```

Adapt limits and configs to your environment and data volumes.
