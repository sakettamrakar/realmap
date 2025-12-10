# Debug Runbook

This document provides operational guidance for diagnosing failures in the scraper, pipeline, and API.

## Common Scenarios

### Scraper fails mid-run

1. Check logs in `runs/run_<id>/logs` and console output.
2. Look for selector errors or CAPTCHA prompts.
3. Re-run with `browser.headless=false` and a small scope (limit filters).
4. Update `search_page.selectors.*` in the config if the RERA portal changed.

### QA shows many mismatches

1. Open `qa_fields/qa_fields_report.md` under the affected run.
2. Inspect HTML in `raw_html/` for a few projects.
3. Confirm parser logic in `parsing/` still matches the page structure.
4. Re-run QA with `--project-key` to zoom in on a single project.

See `QA_GUIDE.md` for full QA workflows.

### Geo coverage is low

1. Run `tools/check_geo_quality.py` and inspect the JSON report.
2. Confirm `normalized_address` is populated for problematic projects.
3. Verify geocoder configuration and rate limits in the YAML config.

See `GEO_PIPELINE.md` and `PHASE4_GEO_OVERVIEW.md` for details.

### Amenity scores look off

1. Run `tools/check_amenity_and_scores_quality.py`.
2. Inspect `ProjectAmenityStats` and `ProjectScores` for a few projects.
3. Confirm amenity provider responses are reasonable.

See `PHASE5_AMENITY_OVERVIEW.md` for deeper context.

### API returns errors

1. Check API logs where FastAPI is running.
2. Verify DB connectivity and migrations.
3. Use `/health` endpoint to verify basic readiness.
4. Confirm environment variables and config paths.

See `API-Reference.md` for endpoints and expected responses.
