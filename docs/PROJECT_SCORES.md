# Project Amenity Scores

This document captures the v1 amenity scoring logic and how to recompute scores for projects with amenity statistics.

## Score definitions

Scores are normalized to a 0–100 range and use simple thresholds from [`docs/PHASE5_AMENITY_DESIGN.md`](./PHASE5_AMENITY_DESIGN.md).

### Daily Needs Score
- **Inputs:** `grocery_convenience` (≤1 km), `supermarket` (≤3 km), `pharmacy` (≤1 km).
- **Per-type rule:** Count 0 → 20, 1–2 → 60, 3–4 → 80, 5+ → 100.
- **Aggregation:** Average sub-scores. Missing types are treated as 0 if no POI was found.

### Connectivity Score
- **Inputs:** `transit_stop` within 3 km and 10 km; `bank_atm` nearest distance as a light proxy for road frontage.
- **Rules:**
  - Transit 3 km: 0 → 20, 1–2 → 60, 3–5 → 80, 6+ → 100.
  - Transit 10 km: 0 → 20, 1–3 → 60, 4–8 → 80, 9+ → 100.
  - Bank/ATM nearest distance: <1 km → 90, 1–2 km → 70, >2 km → 30 (missing distances use the lowest tier).
- **Aggregation:** 70% transit (average of the two transit tiers) + 30% bank/ATM proximity.

### Social Infrastructure Score
- **Inputs:** `school` (≤3 km), `college_university` (≤5 km), `hospital` (≤5 km), `park_playground` (≤3 km), `restaurant_cafe` (≤3 km), `mall` (≤5 km).
- **Rule per type:** Count 0 → 20, 1–2 → 60, 3–5 → 80, 6+ → 100.
- **Aggregation:** Average across types; if both hospitals and schools are absent the score is capped at 70.

### Overall Score
- Weighted blend: 40% daily needs, 35% social infrastructure, 25% connectivity.
- `score_version` is set to `amenity_v1` so future calibrations can co-exist.

## Computing scores

The batch job reads `project_amenity_stats`, applies the scoring model, and upserts results into `project_scores`.

### CLI

```bash
python tools/compute_project_scores.py \
  --limit 100 \
  --log-level INFO
```

**Options:**
- `--limit N` – process only the first `N` projects with amenity stats.
- `--project-id` – restrict to a single project ID.
- `--project-reg` – restrict to a specific registration number (state prefix optional upstream).
- `--recompute` – overwrite existing rows in `project_scores`.
- `--log-level` – verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`).

### Validation & logging
- The job clamps all scores to 0–100 and raises if any component is outside the range.
- Missing amenity slices are tallied and surfaced in logs for QA.
- A small sample of projects is logged with key inputs and resulting scores for sanity checks.

## Data dependencies

- `project_amenity_stats` must contain counts and nearest distances for the amenity types and radii referenced above.
- `project_scores` should exist via migrations; the script will upsert rows and refresh `last_computed_at`.
