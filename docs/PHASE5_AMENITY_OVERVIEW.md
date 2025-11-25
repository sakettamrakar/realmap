# Phase 5: Amenities & Scores Overview

Phase 5 enriches CG RERA projects with nearby amenity context and synthesizes that data into comparable project scores. It builds on Phase 4 geocoding outputs and produces two durable artifacts in the database:

- `project_amenity_stats`: aggregated amenity counts/distances per project, amenity type, and search radius.
- `project_scores`: weighted scores summarizing amenity coverage (connectivity, daily needs, social infrastructure, overall).

## Data flow

```
Projects (Phase 1–3) -> Geocodes (Phase 4) -> Amenity POIs -> Amenity stats -> Project scores
```

1. Projects gain lat/lon in Phase 4 (see GEO docs below).
2. Amenity provider returns nearby POIs for each project coordinate.
3. `compute_project_amenity_stats` aggregates POIs into slices per amenity type + radius.
4. `compute_project_scores` converts the slices into composite scores with versioned weighting.

## Operational runbook

Prerequisites:

- Phase 4 GEO data is populated (`projects.latitude/longitude` present).
- Database schema is migrated (amenity + score tables available).
- `DATABASE_URL` is set, or a config file supplies DB/amenity settings.

Core commands:

- Fetch amenities (optional if cache already populated):
  ```bash
  python tools/fetch_amenities_sample.py --config config.phase2.sample.yaml --limit 10
  ```
- Compute amenity stats (Phase 5 step 1):
  ```bash
  python tools/compute_project_amenity_stats.py --config config.phase2.sample.yaml --limit 50
  ```
- Compute scores (Phase 5 step 2):
  ```bash
  python tools/compute_project_scores.py --limit 50
  ```
- Run amenity/score QA:
  ```bash
  python tools/check_amenity_and_scores_quality.py --output-json runs/amenity_qa_report.json
  ```

Tips:

- Use `--recompute` on the stats/scores commands to refresh existing rows.
- The QA script is safe to run with `--no-write` if you only need the console summary.
- Set `--poi-threshold` and `--radius-km` to tune the anomaly detector for local density.

## References

- [Phase 5 Amenity Design](PHASE5_AMENITY_DESIGN.md)
- [Amenity Provider](AMENITY_PROVIDER.md)
- [Amenity Stats](AMENITY_STATS.md)
- [Project Scores](PROJECT_SCORES.md)
- [Phase 4 GEO Overview](PHASE4_GEO_OVERVIEW.md) / [Phase 4 GEO Design](PHASE4_GEO_DESIGN.md)
