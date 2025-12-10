# Monitoring & QA

This document summarizes operational checks and QA metrics for keeping the pipeline healthy.

## Scraper and QA

- Monitor scraper logs for selector drift and CAPTCHA prompts.
- Use field-by-field QA to detect parsing regressions:
  - `python tools/run_field_by_field_qa.py --run-id <id> --limit 10`
  - Inspect `qa_fields/qa_fields_report.json` and `.md` under the run.
- Watch for sudden spikes in mismatches or missing fields.

## Database and loading

- After each load:
  - Run `python tools/check_db_counts.py` to confirm table counts and basic presence.
  - Check loader logs for upsert failures or schema mismatch warnings.

## Geo QA

- Use `python tools/check_geo_quality.py --output-json runs/geo_qa_report.json --sample-size 5` after geocoding.
- Key metrics:
  - Percentage of projects with valid coordinates.
  - Out-of-bounds coordinates.
  - Distribution of geo precision and providers.

## Amenity and score QA

- Use `python tools/check_amenity_and_scores_quality.py --output-json runs/amenity_qa_report.json`.
- Review:
  - Projects missing amenity stats or scores.
  - Suspiciously low or high counts in key categories.

## API health

- Periodically call `/health` on the API and ensure it returns `{"status": "ok"}`.
- Watch logs for 5xx responses and rate limit events.

These checks can be integrated into CI or basic cron-based monitoring to catch regressions early.
