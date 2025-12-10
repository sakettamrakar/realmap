# Phase 6 Read Model

This document describes the database read model and indexes that back the Phase 6 search, map, and detail endpoints.

## View: `project_search_view`

A lightweight view that centralizes the fields commonly requested by `/projects/search`, `/projects/map`, and export flows.

**Columns**
- `project_id`, `state_code`, `rera_registration_number`, `project_name`
- Admin fields: `district`, `tehsil`, `village_or_locality`, `full_address`
- Canonical geo: `lat`, `lon`, `geo_source`, `geo_precision`, `geo_confidence`
  - Derived from `project_locations` (active rows with the highest confidence) with a fallback to `projects.latitude/longitude`.
- Registration metadata: `registration_date` (`projects.approved_date`), `proposed_end_date`, `extended_end_date`
- Scores: `overall_score`, `location_score`, `amenity_score`, `score_version`
- Amenity rollups: `onsite_available`, `onsite_details`, `total_nearby_count`, `nearest_nearby_km`

**Upstream tables**
- `projects`
- `project_locations` (active rows only)
- `project_scores`
- `project_amenity_stats` (aggregated by project)

The view avoids repeated joins in API code while remaining simple enough for ad-hoc queries.

## Indexes

The following targeted indexes were added to make common Phase 6 filters and sorts efficient:

- `projects(district)`, `projects(tehsil)`, `projects(status)`, `projects(approved_date)` – administrative filters and registration-date sorting.
- `project_scores(overall_score)`, `project_scores(location_score)`, `project_scores(amenity_score)` – score-based filters and ordering.
- `project_locations(lat, lon) WHERE is_active` – bounding-box and radius filters for canonical locations.
- `project_amenity_stats(project_id, radius_km)` – faster aggregation of onsite vs nearby amenity slices.

## Query hints

- Prefer hitting `project_search_view` for list/map endpoints to keep ORM queries lean.
- Apply bounding-box filters on `lat`/`lon` from the view; the active-location index will be used.
- Sorting on `overall_score` or `registration_date` leverages the dedicated indexes.
- Detail endpoints can still fetch related tables directly when richer nested data is needed.
