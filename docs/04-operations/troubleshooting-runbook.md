# Troubleshooting Runbook

This runbook provides scenario-based guidance for diagnosing issues across the scraper, pipelines, and API.

## Scraper issues

### Symptoms

- Crawls terminate early or fetch zero detail pages.
- Logs mention missing selectors or CAPTCHAs.

### Actions

1. Inspect logs in the affected run directory (`logs/`).
2. Re-run with `browser.headless=false` and smaller limits.
3. Verify that `search_page.selectors.*` in your config match the current CG RERA portal.
4. Confirm manual CAPTCHA steps are followed when prompted.

## QA mismatches

### Symptoms

- Sudden increase in field mismatches.
- New fields marked as `missing_in_html` or `missing_in_json`.

### Actions

1. Open `qa_fields/qa_fields_report.md` under the run and inspect a few sample projects.
2. Compare HTML in `raw_html/` to JSON in `scraped_json/` for those projects.
3. Adjust parsing logic in `parsing/` if the RERA page structure has changed.
4. Re-run QA with `--project-key` to focus on a specific project.

## Geo anomalies

### Symptoms

- Many projects lack coordinates.
- Coordinates fall outside expected bounds.

### Actions

1. Run `check_geo_quality.py` to quantify issues and sample problematic records.
2. Confirm `normalized_address` is populated; backfill if needed.
3. Verify geocoder configuration (provider, base URL, rate limits, API key).
4. Consider clearing or regenerating the geocode cache if it is stale.

## Amenity / score anomalies

### Symptoms

- Projects missing amenity stats or scores.
- Highly skewed amenity counts.

### Actions

1. Run `check_amenity_and_scores_quality.py`.
2. Inspect a few projects in the DB for their amenity stats and scores.
3. Confirm amenity provider responses are reasonable and not rate limited.

## API errors

### Symptoms

- `/health` fails or returns non-OK.
- Requests to project endpoints return 5xx errors.

### Actions

1. Check API logs where FastAPI is running.
2. Confirm the API can connect to the database (check `DATABASE_URL`).
3. Verify that migrations have been applied and tables exist.
4. Re-run key health checks and DB verification tools.

Many of these scenarios are covered in more detail in the historical debug and QA docs; this runbook aims to provide a concise, operations-focused summary.
