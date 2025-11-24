# Project amenity stats job

This job computes the Phase 5 amenity metrics for each project that already has latitude/longitude values. For every configured `(amenity_type, radius_km)` slice it stores:

- `count_within_radius`
- `nearest_distance_km`

The default slices align with the taxonomy and radii outlined in `docs/PHASE5_AMENITY_DESIGN.md`.

## How it works
- Uses the amenity provider + cache layer from Phase 5 A3 to fetch POIs and reuse nearby results via the `amenity_poi` table (including the `search_radius_km` column to gate reuse).
- Computes metrics with `cg_rera_extractor.amenities.stats.compute_project_amenity_stats`, then writes rows to `project_amenity_stats` with a provider snapshot.
- Skips projects that already have stats unless `--recompute` is supplied (which deletes existing slices before recomputing).
- Logs provider call counts vs. cache hits to highlight reuse benefits.

## Running the batch job

Small smoke test for a few projects:

```bash
python tools/compute_project_amenity_stats.py --limit 5
```

Recompute for a specific project ID, forcing fresh stats:

```bash
python tools/compute_project_amenity_stats.py --project-id 123 --recompute
```

Full recompute for all projects with coordinates (uses provider from config or `DATABASE_URL`):

```bash
python tools/compute_project_amenity_stats.py --recompute
```

Use a custom config file (overriding DB + amenity provider settings):

```bash
python tools/compute_project_amenity_stats.py --config config.example.yaml
```

## Operational notes
- The cache tracks `last_seen_at` and the maximum `search_radius_km` seen per POI; a wider initial search enables cache hits for subsequent smaller radii.
- Provider and cache hit counters surface in logs to estimate Overpass usage.
- The job is safe to re-run; it only inserts missing slices by default and can overwrite existing ones with `--recompute`.
