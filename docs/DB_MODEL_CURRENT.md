# Current Database Model

> **Last Updated**: December 10, 2024 (Data Audit Implementation)

## Overview
The database schema is implemented in PostgreSQL using SQLAlchemy ORM. It consists of a central `projects` table and several child tables.

## Tables

### 1. `projects` (42 columns)
- **Primary Key**: `id` (Integer).
- **Natural Key**: `state_code` + `rera_registration_number` (Unique Constraint).
- **Core Columns**:
    - `project_name`, `status`, `district`, `tehsil`, `village_or_locality`, `full_address`.
    - `pincode`, `latitude`, `longitude` (Geocoding fields).
    - `approved_date`, `proposed_end_date`, `extended_end_date`.
    - `raw_data_json` (JSON): Stores the entire V1 JSON blob.
- **GEO Columns**:
    - `geo_source`, `geo_precision`, `geo_confidence`, `geo_normalized_address`, `geo_formatted_address`.
- **QA Columns**:
    - `qa_flags` (JSON), `qa_status`, `qa_last_checked_at`.
    - `scraped_at`, `data_quality_score`, `last_parsed_at`.
- **New Columns (2024-12-10)**:
    - `project_website_url` - Project marketing website.
    - `number_of_phases` - Number of phases (default: 1).
    - `fsi_approved`, `far_approved` - Floor space/area ratios.
    - `has_litigation` - Boolean flag for pending litigations.
    - `open_space_area_sqmt`, `approved_building_coverage`.
    - `total_complaints`, `complaints_resolved`.
    - `locality_id` - FK to localities table.
- **Relationships**: One-to-many with all child tables.

### 2. `promoters` (10 columns)
- **Columns**: `promoter_name`, `promoter_type`, `email`, `phone`, `address`, `website`.
- **New Columns (2024-12-10)**: `gst_number`, `authorized_signatory`.
- **Foreign Key**: `project_id`.

### 3. `buildings` (14 columns)
- **Columns**: `building_name`, `building_type`, `number_of_floors`, `total_units`, `status`.
- **New Columns (2024-12-10)**: 
    - `basement_floors`, `stilt_floors`, `podium_floors`.
    - `height_meters`, `plan_approval_number`.
    - `parking_slots_open`, `parking_slots_covered`.
- **Foreign Key**: `project_id`.

### 4. `project_unit_types` (~26 columns)
- **Columns**: `unit_label`, `unit_type`, `bedroom_count`, carpet/builtup/SBUA areas (min/max in sqft and sqm).
- **New Columns (2024-12-10)**:
    - `balcony_area_sqft`, `common_area_sqft`, `terrace_area_sqft`.
    - `open_parking_price`, `covered_parking_price`, `club_membership_fee`.
- **Foreign Key**: `project_id`.
- **Note**: Replaces legacy `unit_types` table.

### 5. `project_artifacts` (~12 columns)
- **Columns**: `category`, `artifact_type`, `file_path`, `source_url`, `is_preview`.
- **New Column (2024-12-10)**: `document_type_id` - FK to `document_types`.
- **Foreign Key**: `project_id`.
- **Note**: Stores all project documents, images, and media.

### 6. `quarterly_updates` (13 columns)
- **Columns**: `quarter`, `update_date`, `status`, `summary`, `raw_data_json`.
- **New Columns (2024-12-10)**:
    - `foundation_percent`, `plinth_percent`, `superstructure_percent`.
    - `mep_percent`, `finishing_percent`, `overall_percent`.
- **Foreign Key**: `project_id`.

### 7. `bank_accounts` (11 columns)
- **Columns**: `bank_name`, `branch_name`, `account_number`, `ifsc_code`, `account_holder_name`.
- **New Columns (2024-12-10)**:
    - `account_type`, `authorized_signatories`.
    - `total_funds_received`, `total_funds_utilized`.
- **Foreign Key**: `project_id`.

### 8. `land_parcels` (10 columns)
- **Columns**: `survey_number`, `area_sqmt`, `owner_name`, `encumbrance_details`.
- **New Columns (2024-12-10)**: `ward_number`, `mutation_number`, `patwari_halka`, `plot_number`.
- **Foreign Key**: `project_id`.

### 9. `project_scores` (17 columns)
- **Columns**: `connectivity_score`, `daily_needs_score`, `social_infra_score`, `overall_score`, `location_score`.
- `amenity_score`, `value_score`, `lifestyle_score`, `safety_score`, `environment_score`, `investment_potential_score`.
- `score_version`, `last_computed_at`, `score_status`, `score_status_reason`, `structured_ratings`.
- **Foreign Key**: `project_id`.

### 10. `project_pricing_snapshots` (17 columns)
- **Columns**: Pricing history with `unit_type_label`, `min_price_total`, `max_price_total`, `min_price_per_sqft`, `max_price_per_sqft`.
- `price_per_sqft_carpet_min/max`, `price_per_sqft_sbua_min/max`.
- `source_type`, `source_reference`, `snapshot_date`, `is_active`.
- **Foreign Key**: `project_id`.

### 11. `localities` (12 columns) - NEW
- **Purpose**: Location normalization taxonomy.
- **Columns**: `name`, `slug` (unique), `district`, `state_code`, `lat`, `lon`, `pincode`, `locality_type`, `parent_locality_id`.
- **Indexes**: `ix_localities_district`, `ix_localities_pincode`.

### 12. `document_types` (6 columns) - NEW
- **Purpose**: Document classification lookup.
- **Columns**: `code` (unique), `name`, `category`, `is_required`, `display_order`.
- **Seed Data**: 14 standard document types (registration_certificate, building_plan, fire_noc, etc.).

### 13. `data_provenance` (~12 columns)
- **Purpose**: Audit trail for data extraction.
- **Columns**: `snapshot_url`, `source_domain`, `extraction_method`, `parser_version`, `confidence_score`, `scraped_at`, `run_id`.
- **Foreign Key**: `project_id`.

## Mapping & Loader Logic
- **Upsert**: Projects are upserted based on `state_code` + `rera_registration_number`.
- **Child Entities**: Child records (promoters, buildings, etc.) are **deleted and re-inserted** on every load.
- **Raw Data**: The full V1 JSON is saved into `projects.raw_data_json`.
- **QA Validation**: QA flags and status are computed and stored on each load.
- **Provenance**: Data provenance records are created for each project load.

## Resolved Issues (2024-12-10)

| Issue | Status | Fix |
|-------|--------|-----|
| `bank_details` not stored | ✅ Fixed | `bank_accounts` table populated from ETL |
| `land_details` not stored | ✅ Fixed | Loader now uses `v1_project.land_details` |
| `project_documents` empty | ✅ Fixed | Replaced with `project_artifacts`, populated from previews |
| Date fields always NULL | ✅ Fixed | Added `_normalize_date()` function |
| `scraped_at` always NULL | ✅ Fixed | Set from metadata or current time |
| `village_or_locality` empty | ✅ Fixed | Added key variants + extraction |
| `pincode` empty | ✅ Fixed | Added `_extract_pincode()` function |

## Remaining Normalization Opportunities
- `district` and `tehsil` could link to `localities` table.
- `status` could be an enum.
- Consider moving to upsert pattern for child tables (vs delete+insert).
