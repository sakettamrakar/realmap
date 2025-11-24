# Phase 5 Amenity Intelligence Design

## Goals
- Enrich CG RERA projects with nearby amenities to power location intelligence and buyer-facing insights.
- Compute per-project amenity stats (counts within radii, nearest distance) and simple scores (connectivity, daily needs, social infrastructure).
- Introduce database structures that are reusable for multiple providers and future UI filters without altering the existing project ingestion flow.

## Current GEO foundation (Phase 4)
- Projects already store `latitude`/`longitude`, `normalized_address`, and geocoder metadata introduced in Phase 4; these are sufficient to run location queries.【F:docs/PHASE4_GEO_DESIGN.md†L5-L122】
- The geocoding pipeline is operational with provider abstraction and caching, letting us geocode remaining projects and maintain coordinates.【F:docs/PHASE4_GEO_OVERVIEW.md†L10-L87】
- Current DB snapshot shows small sample data (2 projects), but the schema accommodates larger volumes via `projects` as the anchor entity.【F:db_inspection.txt†L1-L9】

## Amenity taxonomy and default search radii (v1)
| Amenity type | Description / examples | Default radii (km) |
| --- | --- | --- |
| school | Primary/secondary schools | 1, 3, 5 |
| college_university | Colleges, universities, polytechnics | 3, 5, 8 |
| hospital | Multispecialty hospitals | 1, 3, 5 |
| clinic | Small clinics, diagnostic centers | 1, 3 |
| pharmacy | Chemists/medical stores | 0.5, 1, 2 |
| supermarket | Supermarkets and hypermarkets | 1, 3 |
| grocery_convenience | Kirana/mini-markets/convenience stores | 0.5, 1, 2 |
| mall | Shopping malls | 3, 5, 8 |
| bank_atm | Banks and ATMs | 0.5, 1, 2 |
| restaurant_cafe | Restaurants, cafés, quick service | 1, 3, 5 |
| park_playground | Parks, playgrounds, open spaces | 1, 3, 5 |
| transit_stop | Bus stops, metro stations, railway stations | 1, 3, 5, 10 |

Notes:
- Radii are ordered for coarse-to-fine stats; we can subset per score dimension.
- Types are deliberately concise to simplify scoring and UI filters; provider-specific categories will map to this taxonomy.

## Data source and enrichment strategy
- **Providers:** Support a provider abstraction similar to Phase 4, starting with **OSM/Overpass** (cost-free, permissive) and optionally **Google Places** for higher precision where budget permits.
- **Acquisition mode:** Maintain a **local POI cache** to avoid duplicate provider calls. Workflow:
  1) Query provider for a bounding box or radius around project coordinates per amenity type.
  2) Upsert POIs into a shared `amenity_poi` table keyed by `(provider, provider_place_id)`.
  3) Compute per-project stats by spatially joining project coordinates with cached POIs; refresh cache periodically (e.g., monthly) or on-demand.
- **Reuse:** Multiple projects in proximity reuse the same cached POIs, reducing cost and enabling QA on POI quality.

## Database schema additions
### `amenity_poi`
- **Purpose:** Cache/place table of provider POIs to be reused across projects and scoring runs.
- **Columns:**
  - `id` (PK)
  - `provider` (`text`) — e.g., `osm`, `google`.
  - `provider_place_id` (`text`, unique with provider) — stable provider identifier.
  - `amenity_type` (`text`) — normalized taxonomy value (table above).
  - `name` (`text`)
  - `lat` (`numeric(9,6)`), `lon` (`numeric(9,6)`)
  - `formatted_address` (`text`)
  - `source_raw` (`jsonb`) — raw provider payload for audit/mapping.
  - `last_seen_at` (`timestamptz`) — last time fetched/validated.
  - `created_at`, `updated_at` (`timestamptz`)
- **Indexes:** composite `(amenity_type, lat, lon)` for spatial proximity (or future PostGIS index), `(provider, provider_place_id)` unique.

### `project_amenity_stats`
- **Purpose:** Store per-project stats per amenity type and radius for reuse by UI and scoring.
- **Columns:**
  - `id` (PK)
  - `project_id` (FK → projects.id, cascade delete)
  - `amenity_type` (`text`)
  - `radius_km` (`numeric(4,2)`)
  - `count_within_radius` (`integer`)
  - `nearest_distance_km` (`numeric(6,3)`, nullable if none)
  - `provider_snapshot` (`text`, optional) — provider(s)/cache version used for computation.
  - `last_computed_at` (`timestamptz`)
- **Uniqueness:** `(project_id, amenity_type, radius_km)` to keep the latest stat per slice.

### `project_scores`
- **Purpose:** Persist simple composite scores per project for UI consumption and comparisons.
- **Columns:**
  - `id` (PK)
  - `project_id` (FK → projects.id, unique)
  - `connectivity_score` (`integer`, 0–100)
  - `daily_needs_score` (`integer`, 0–100)
  - `social_infra_score` (`integer`, 0–100)
  - `overall_score` (`integer`, 0–100)
  - `score_version` (`text`) — e.g., `v1.0` to allow future recalibration.
  - `last_computed_at` (`timestamptz`)

### Relationships & workflow
- `projects` retain lat/lon from Phase 4. Stats are computed by querying `amenity_poi` within radii around project coordinates.
- `project_amenity_stats` is regenerated when the cache or scoring version changes; consumers read the latest row per `(project, amenity_type, radius)`.
- `project_scores` depends on `project_amenity_stats`; a scoring job updates both tables.

## Scoring model (v1, simple thresholds)
Scores are normalized to 0–100 via tiered thresholds; ties favor higher availability. Thresholds assume the default radii indicated.

### Daily needs score (weights toward immediate essentials)
- Inputs (radius hints in parentheses):
  - `grocery_convenience` (<=1 km), `supermarket` (<=3 km), `pharmacy` (<=1 km).
- Rule: assign sub-scores per amenity type using counts; average them.
  - Count 0 → 20, 1–2 → 60, 3–4 → 80, 5+ → 100.
- Daily needs score = average of available sub-scores (missing types treated as 0 if no POI found).

### Connectivity score
- Inputs:
  - `transit_stop` within 3 km and 10 km (captures local bus/metro and intercity rail).
  - Optionally nearest distance to `bank_atm` as proxy for main road frontage (lighter weight).
- Rules:
  - Transit count within 3 km: 0 → 20, 1–2 → 60, 3–5 → 80, 6+ → 100.
  - Transit count within 10 km: 0 → 20, 1–3 → 60, 4–8 → 80, 9+ → 100.
  - Bank/ATM nearest distance: >2 km → 30, 1–2 km → 70, <1 km → 90.
- Connectivity score = weighted blend: 70% transit (average of 3 km & 10 km tiers), 30% bank/ATM proximity.

### Social infrastructure score
- Inputs:
  - `school` (<=3 km), `college_university` (<=5 km), `hospital` (<=5 km), `park_playground` (<=3 km), `restaurant_cafe` (<=3 km), `mall` (<=5 km).
- Rules (per type):
  - Count 0 → 20, 1–2 → 60, 3–5 → 80, 6+ → 100.
- Social infra score = average across available types, with optional caps if hospitals/schools are missing (e.g., cap at 70 if both hospital and school counts are 0).

### Overall score
- Weighted aggregate: 40% daily needs, 35% social infra, 25% connectivity.
- Store `score_version` to allow future recalibration without ambiguity.

## Operational considerations
- **Caching & refresh cadence:** Reuse `amenity_poi` aggressively; schedule monthly refreshes to avoid stale openings/closures. Invalidation via `last_seen_at` and provider snapshot.
- **Provider limits:** Overpass is rate-limited; batch queries by bounding boxes and amenity type. Google usage should be gated by config flags and quotas.
- **Spatial calculations:** Start with Haversine distance in-app; migrate to PostGIS later for performant radial queries and indexes.
- **UI readiness:** `project_amenity_stats` supports filters like “projects with 3+ schools within 3 km” or “nearest hospital distance.” `project_scores` fuels badges and sort orders.
