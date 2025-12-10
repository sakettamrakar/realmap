# Phase 6 QA Checklist

This checklist mirrors the manual steps used during Phase 6 verification. It pairs ad-hoc checks with helper scripts so you can spot issues quickly across the DB, read-model, and API layers.

## Quick commands

- End-to-end smoke: `python tools/dev_phase6_smoke_test.py`
- Read-model sanity: `python tools/check_search_read_model.py [--district <District>]`
- Amenity/score QA: `python tools/check_amenity_and_scores_quality.py --sample-size 5`

## Manual QA steps

1. **Environment sanity**
   - Ensure `DATABASE_URL` is set and points at the loaded Phase 6 database.
   - Run `python tools/dev_phase6_smoke_test.py --limit 4`.
   - Confirm output shows all required tables (`projects`, `project_scores`, `project_amenity_stats`, `project_locations`) present.

2. **Search experience**
   - In the smoke test output, verify per-district search scenarios report `sorted_ok=True` and include the sampled project.
   - Manually call the search API if desired: `uvicorn cg_rera_extractor.api.app:app --reload` then `GET /projects/search?district=<district>&sort_by=overall_score`.
   - Spot-check that high scores appear first and that pagination looks reasonable.

3. **Project detail completeness**
   - From the smoke test’s sample projects, confirm `overall/location/amenity` scores are non-null.
   - Verify `lat/lon` is present and `geo_quality` or `geo_source` are populated.
   - Ensure amenity context separates onsite counts vs. nearby summaries (onsite list present alongside nearby_summary map).

4. **Map layer**
   - From the smoke test’s map spot-checks, confirm each bbox returns pins (>0) around the sampled districts.
   - If running the API server, hit `/projects/map?bbox=<min_lat,min_lon,max_lat,max_lon>` for one of the bboxes printed by the smoke test and confirm pins render in the UI.

5. **Amenity + score QA**
   - Run `python tools/check_amenity_and_scores_quality.py --sample-size 5`.
   - Review the JSON/console output for null scores, missing amenity slices, or mismatched onsite vs. nearby counts.

6. **Read-model integrity**
   - Run `python tools/check_search_read_model.py --district <district>` to ensure `project_search_view` is populated.
   - Confirm the plan output for the bbox query looks indexed (Index Scan vs. Seq Scan) and that the sample queries return rows with scores.

7. **Regression sniff test**
   - Re-run `python tools/dev_phase6_smoke_test.py --skip-api` if you change scoring or amenity logic to make sure DB + services still align.

## Expected results

- All four core tables exist with no missing columns.
- Sample projects include coordinates, scores, onsite amenity counts, and nearby summaries.
- Search scenarios report sorted results and include the sampled project.
- Map spot-checks return at least one pin inside each bbox.
- Amenity/score QA shows zero or a short list of issues after pipeline updates.
