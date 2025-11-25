# Amenities vs. Location Context

## Conceptual Split

We clearly distinguish between **Project Amenities** (internal/onsite) and **Location Context** (external/nearby).

### 1. Project Amenities (Onsite)
*   **Definition**: Features and infrastructure provided *within* the project boundary by the developer.
*   **Examples**: Clubhouse, internal roads, water supply, sewage treatment plant, power backup, security, swimming pool, gym, landscaped gardens.
*   **Data Sources**: RERA filings (`project_amenities_rera`), builder websites, brochures, manual entry.
*   **Scoring**: `amenity_score`. Reflects the quality of life *inside* the complex.

### 2. Location Context (Nearby)
*   **Definition**: Points of Interest (POIs) and infrastructure *outside* the project boundary in the surrounding neighborhood.
*   **Examples**: Schools, hospitals, bus stops, metro stations, malls, supermarkets, parks, restaurants.
*   **Data Sources**: External providers (Google Places, OSM), manual POI entry.
*   **Scoring**: `location_score`. Reflects the connectivity and convenience of the *neighborhood*.

## Scoring Model

The `overall_score` is a composite of these two distinct pillars (plus potentially others in the future).

### Amenity Score (Onsite)
*   Derived from `ProjectAmenityStats` fields prefixed with `onsite_`.
*   Focuses on the presence/absence and quality of essential and luxury onsite facilities.

### Location Score (Nearby)
*   Derived from `ProjectAmenityStats` fields prefixed with `nearby_`.
*   Focuses on proximity and density of external services (e.g., "3 schools within 3km").
*   Sub-components:
    *   `connectivity_score` (Transit, Roads)
    *   `social_infra_score` (Schools, Hospitals, Malls)
    *   `daily_needs_score` (Grocery, Pharmacy)

### Overall Score
*   `overall_score` = Weighted combination of `amenity_score` and `location_score`.

## Data Model Changes

### `project_amenity_stats`
We split the generic stats into specific buckets:
*   **Onsite**: `onsite_available` (bool), `onsite_count` (int), `onsite_details` (JSON).
*   **Nearby**: `nearby_count_1km`, `nearby_count_3km`, `nearby_nearest_km`.

### `project_scores`
*   New columns: `amenity_score`, `location_score`.
*   Existing columns (`connectivity`, `daily_needs`, `social_infra`) become sub-components of `location_score`.
