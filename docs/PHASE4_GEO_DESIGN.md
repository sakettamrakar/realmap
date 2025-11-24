# Phase 4 GEO Design

This document enumerates the GEO columns that must exist on the `projects` table to support geocoding and downstream location-aware features. All fields are nullable for incremental rollout.

## GEO Columns

| Column | Type | Notes |
| --- | --- | --- |
| `latitude` | `NUMERIC(9,6)` | Decimal degrees; existing field remains canonical for lat. |
| `longitude` | `NUMERIC(9,6)` | Decimal degrees; existing field remains canonical for lon. |
| `geocoding_status` | `VARCHAR(64)` | Lifecycle flag (`NOT_GEOCODED`, `PENDING`, `SUCCESS`, `FAILED`). |
| `geocoding_source` | `VARCHAR(64)` | Legacy source tag used by earlier geocoding flow; retained for compatibility. |
| `geo_source` | `VARCHAR(128)` | Canonical source/provider for GEO data (e.g., `MAPBOX`, `GOOGLE`, `MANUAL`). Prefer this going forward; keep `geocoding_source` populated for backwards compatibility. |
| `geo_precision` | `VARCHAR(32)` | Qualitative precision level such as `ROOFTOP`, `LOCALITY`, `CITY_CENTROID`. |
| `geo_confidence` | `NUMERIC(4,3)` | Confidence score in range `0.000`–`1.000` when provided by the geocoder. |
| `geo_normalized_address` | `VARCHAR(512)` | Normalized/searchable address string used as geocoding input. |
| `geo_formatted_address` | `VARCHAR(512)` | Canonical formatted address returned by the geocoder. |

> Clarification: The project previously stored `geocoding_source`; `geo_source` is the preferred name but both columns should co-exist until loaders and services converge on the canonical field.
