# Data Model

**Version:** 1.0.0
**Date:** 2025-12-12

---

## 1. Database Schema
RealMap uses **PostgreSQL**. The schema centers around the `projects` table.

### Core Tables

#### `projects`
The master record for a real estate project.
*   `id` (PK): Integer.
*   `rera_id` (Unique): The official registration number (e.g., `PCGRERA...`).
*   `name`: Project name.
*   `raw_data_json`: The original scraped JSON payload (NoSQL-style).
*   `geo_location`: PostGIS Point(lat, lon).
*   `overall_score`: Computed quality score (0-100).

#### `buildings`
Physical structures within a project.
*   `project_id` (FK): Link to Project.
*   `floors`: Number of floors.
*   `apartments`: Total units.

#### `project_unit_types`
Unit configurations (Floorplans).
*   `project_id` (FK).
*   `type`: (e.g., "3BHK").
*   `carpet_area_sqft`: Normalized area.
*   `price_range`: Min/Max price estimates.

#### `project_documents`
Legal and marketing files.
*   `url`: Path to the file.
*   `type`: (Brochure, Approval, Litigation).

---

## 2. Enrichment Tables

#### `project_scores`
Granular scores computed by the Amenity Engine.
*   `connectivity_score`
*   `lifestyle_score`
*   `safety_score`
*   `value_score`

#### `amenity_stats`
Aggregated counts of nearby POIs.
*   `schools_within_2km`
*   `hospitals_within_5km`

---

## 3. Data Flow & Provenance

### V1 JSON Schema
Between the Scraper and the Database, data exists as **V1 JSON**.
*   **Path:** `runs/<run_id>/scraped_json/*.v1.json`
*   **Structure:**
    ```json
    {
      "rera_id": "...",
      "project_details": { ... },
      "promoter_details": { ... }
    }
    ```

### Provenance Tracking
Every insert into `projects` creates a `data_provenance` record:
*   `source_url`: URL scraped.
*   `scraped_at`: Timestamp.
*   `scraper_version`: Implementation version.

---

## 4. Related Documents
- [Architecture](./Architecture.md)
- [Scraper Pipeline](./Scraper_Pipeline.md)
