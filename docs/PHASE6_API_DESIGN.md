# Phase 6: API & UX Contracts

This document defines the external-facing contracts for querying CG RERA projects and their enriched context. It targets two audiences: an internal analyst-facing API and a future UI surface (map + list).

## User types
1. **Internal analyst / data engineer**: needs flexible filters, ranking pivots, CSV exports, and debug hooks to validate geo/amenity data quality.
2. **Future UI / app**: powers a map + list experience with filters, highlights, and a project detail page.

## Key use cases (examples)
1. Search projects in Raipur with budget band (e.g., 50–80L once pricing is available), within 5 km of a pin, sorted by `overall_score`.
2. Filter for residential projects with high `location_score` (e.g., >0.7) and on-site clubhouse + parking, then show them on the map and list.
3. Open a project detail page: show RERA metadata, canonical geo with source quality, on-site amenities, aggregated amenity/location stats, and scores.
4. Show a map of all projects in a bounding box, pins colored by `overall_score` and sized by project size (units/area).
5. Compare two projects side by side for an internal review (scores, amenity coverage, nearby schools/hospitals, geo confidence).
6. Export a CSV of all projects in Durg with their scores and amenity counts for offline analysis.
7. Debug a specific project’s geo lineage and amenity aggregation (raw sources, matching status, QA flags).
8. Retrieve nearby points of interest for a project to render a location context card (top N schools/hospitals).

## API surface (proposed, internal for now)
- REST over HTTP using FastAPI, module `cg_rera_extractor.api`.
- JSON for requests/responses. Pagination via `page` + `page_size` (default page_size=20, max=200).
- Auth: assumed internal token header `X-Internal-Key` (pluggable later).

### `GET /projects/search`
Supports list + map views.

**Query params**
- `district` / `tehsil`: optional administrative filters.
- `lat`, `lon`, `radius_km`: optional radial filter (Haversine on canonical `projects.lat/lon`).
- `bbox`: alternative to radius, `min_lat,min_lon,max_lat,max_lon`.
- `project_type`: `residential|commercial|mixed` (derived from `projects` / RERA use type).
- `status`: registration/status filters (from `projects.status` or RERA status fields).
- `amenities`: comma list of required on-site amenities (matched against normalized amenity set in `project_amenity_stats`).
- `min_overall_score`, `min_location_score`, `min_amenity_score`: score thresholds (from `project_scores`).
- `min_units` / `max_units` or `min_area` / `max_area`: coarse size filters (from `projects` or `project_amenity_stats` if available).
- `sort`: one of `overall_score` (default), `location_score`, `amenity_score`, `registration_date`, `distance`, `units`, `area`.
- `page`, `page_size`.

**Response shape (list items)**
```json
{
  "page": 1,
  "page_size": 20,
  "total": 123,
  "items": [
    {
      "project_id": "uuid",
      "name": "Project Name",
      "district": "Raipur",
      "tehsil": "Raipur",
      "project_type": "residential",
      "status": "Registered",
      "lat": 21.25,
      "lon": 81.63,
      "geo_quality": "canonical|geocoder|manual",
      "overall_score": 0.81,
      "location_score": 0.76,
      "amenity_score": 0.72,
      "units": 120,
      "area_sqft": 150000,
      "registration_date": "2023-06-01",
      "distance_km": 3.4,
      "highlight_amenities": ["clubhouse", "parking"],
      "onsite_amenity_counts": {"total": 15, "primary": 6},
      "nearby_counts": {"schools": 5, "hospitals": 2}
    }
  ]
}
```

**Table mapping**
- Base project metadata: `projects`.
- Canonical geo & source: `project_locations` joined to `projects`.
- Scores: `project_scores` (overall/location/amenity).
- Aggregated amenity stats: `project_amenity_stats` (counts + availability flags).
- Distance filter: computed from canonical `projects.lat/lon`.
- Status/registration date: from `projects` / RERA fields.

**Indexing/perf notes**
- Spatial index on `projects` or `project_locations` (`geometry/POINT`) for radius/bbox queries.
- B-tree indexes on `district`, `tehsil`, `project_type`, `status`, `registration_date`.
- Partial indexes on score columns for common thresholds (`overall_score`, `location_score`).
- Consider materialized view for list payload combining `projects + project_scores + project_amenity_stats` to avoid repeated joins.

### `GET /projects/{project_id}`
Detail view for UI and analysts.

**Path params**
- `project_id`: UUID or internal ID.

**Query params**
- `include_raw`: boolean (default `false`) to attach raw source snippets for QA.
- `nearby_limit`: int (default 5) for top-N POIs per category.

**Response shape**
```json
{
  "project": {
    "project_id": "uuid",
    "name": "Project Name",
    "rera_number": "CG-XXXX",
    "developer": "Builder Name",
    "project_type": "residential",
    "status": "Registered",
    "registration_date": "2023-06-01",
    "expected_completion": "2025-12-31",
    "rera_fields": { /* normalized RERA metadata */ }
  },
  "location": {
    "lat": 21.25,
    "lon": 81.63,
    "geo_source": "geocoder|manual|rera",
    "geo_confidence": "high|medium|low",
    "address": "...",
    "district": "Raipur",
    "tehsil": "Raipur"
  },
  "scores": {
    "overall_score": 0.81,
    "location_score": 0.76,
    "amenity_score": 0.72,
    "scoring_version": "v1.0"
  },
  "amenities": {
    "onsite_list": ["clubhouse", "parking", "gym"],
    "onsite_counts": {"total": 15, "primary": 6, "secondary": 9},
    "nearby_summary": {
      "schools": {"count": 5, "avg_distance_km": 2.3},
      "hospitals": {"count": 2, "avg_distance_km": 3.1},
      "transit": {"count": 3, "avg_distance_km": 1.2}
    },
    "top_nearby": {
      "schools": [{"name": "ABC School", "distance_km": 1.2}],
      "hospitals": [{"name": "City Hospital", "distance_km": 2.0}],
      "transit": [{"name": "Metro Stop", "distance_km": 1.0}]
    }
  },
  "qa": {
    "geo_notes": "manual override from QA",
    "amenity_notes": "merged builder + RERA list",
    "issues": ["geo_low_confidence"]
  },
  "raw": {
    "rera_page": "...",
    "builder_brochure": "...",
    "geocoder_response": {}
  }
}
```

**Table mapping**
- `projects`: core RERA fields and developer info.
- `project_locations`: canonical lat/lon, source, confidence, admin fields.
- `project_scores`: overall/location/amenity scores + version.
- `project_amenity_stats`: onsite counts and normalized amenity lists.
- POI aggregates: `project_amenity_stats` (summaries) plus derived nearby tables (e.g., `project_nearby_pois` if present).
- Raw hooks: `project_raw_sources` (if available) or S3 pointers stored on project.

### `GET /projects/map`
Lightweight pin feed for map tiles; optimized for bounding box queries.

**Query params**
- `bbox` (required): `min_lat,min_lon,max_lat,max_lon`.
- `min_overall_score` (optional) to reduce clutter.
- `project_type` / `status` (optional) for filtering.
- `zoom`: integer to allow payload shaping (e.g., clustering thresholds later).

**Response shape**
```json
{
  "items": [
    {
      "project_id": "uuid",
      "name": "Project Name",
      "lat": 21.25,
      "lon": 81.63,
      "overall_score": 0.81,
      "project_type": "residential",
      "status": "Registered",
      "size_hint": {"units": 120, "area_sqft": 150000}
    }
  ]
}
```

**Table mapping**
- `project_locations` + `projects` for geo + labels.
- `project_scores` for pin coloring/filters.
- `project_amenity_stats` or `projects` for size hints.

**Perf notes**
- Use spatial index and WHERE bbox to avoid full scan.
- Future: server-side clustering for high zoom levels.

### `GET /projects/{project_id}/nearby`
Convenience endpoint for location context cards.

**Query params**
- `categories`: comma list (default `schools,hospitals,transit`).
- `limit`: per-category limit (default 5).
- `max_distance_km`: optional distance cap.

**Response shape**
```json
{
  "project_id": "uuid",
  "categories": {
    "schools": [{"name": "ABC", "distance_km": 1.2}],
    "hospitals": [{"name": "City Hospital", "distance_km": 2.0}]
  }
}
```

**Table mapping**
- Precomputed nearby tables or views (`project_nearby_pois`, `project_amenity_stats` summaries). Fallback: live spatial query against POI table.

### Internal analyst endpoints / flows
1. **`GET /internal/projects/export`**
   - Params: same filters as `/projects/search`; response as CSV stream with all score + amenity fields.
   - Use for offline analysis or sharing.
2. **`GET /internal/projects/{project_id}/debug`**
   - Returns: geo lineage (sources, QA overrides), amenity lineage (per-source lists), scoring inputs (feature vector), and validation flags.
3. **CLI helper**: `python -m cg_rera_extractor.api.export --district Raipur --min_overall_score 0.7 --out raipur_highscore.csv` to mirror the export endpoint.

## Data field glossary (API-facing)
- `overall_score`, `location_score`, `amenity_score`: from `project_scores` (float 0–1, with `scoring_version`).
- `geo_source`: enum of `rera|geocoder|manual|inferred`; `geo_confidence`: `high|medium|low` from QA pipeline.
- `onsite_amenities`: normalized strings; counts broken into `primary` vs `secondary` per `project_amenity_stats` definition.
- `nearby_counts`: aggregated POI counts per category within a default radius (e.g., 5 km) stored in `project_amenity_stats`.
- `distance_km`: computed on request when a lat/lon filter is provided.

## Performance & reliability considerations
- **Indexes**: spatial (`GIST` on `project_locations.geom`), B-tree on `district`, `tehsil`, `project_type`, `status`, `registration_date`, and score columns used for sorting/thresholds.
- **Materialized views**: create `project_search_mv` combining `projects`, `project_scores`, `project_amenity_stats`, and canonical geo for faster list queries; refresh nightly or on pipeline completion.
- **Pagination**: enforce `page_size` limits; consider keyset pagination for deep scroll on map/list.
- **Caching**: short-lived cache (Redis) for map tiles and repeated searches with identical params.
- **Error handling**: structured errors with codes (`INVALID_FILTER`, `NOT_FOUND`, `RATE_LIMITED`).
- **Versioning**: prefix routes with `/v1`; include `scoring_version` in responses for auditability.

## Module layout (proposed)
- `cg_rera_extractor.api.router`: FastAPI routers for `/projects` and `/internal`.
- `cg_rera_extractor.api.schemas`: Pydantic models for request/response shapes.
- `cg_rera_extractor.api.deps`: DB session + auth dependencies.
- `cg_rera_extractor.api.services.search`: query builder hitting materialized view and applying geospatial filters.
- `cg_rera_extractor.api.services.detail`: orchestrates detail payload, including POI summaries.
- `cg_rera_extractor.api.services.export`: CSV export + CLI entrypoint.

## Open questions / next steps
- Pricing integration: once price bands exist, add `min_price`/`max_price` and `price_per_sqft` filters.
- Clustering: server-side cluster or vector tile generation for map at scale.
- Access control: whether to expose debug/raw endpoints outside internal network.
- SLAs: define latency targets (e.g., <400 ms for search/list, <300 ms for map pins).
