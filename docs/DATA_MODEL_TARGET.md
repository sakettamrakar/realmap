# Target Data Model & Storage Strategy

## Logical Model

The improved data model aims to capture all scraped data structurally while maintaining traceability to source artifacts.

### Entities

1.  **Project**: The central entity. Uniquely identified by `state_code` and `rera_registration_number`.
2.  **Promoter**: The entity developing the project. (One-to-Many with Project).
3.  **BankAccount**: RERA designated bank accounts. (One-to-Many).
4.  **LandParcel**: Details about the land (area, location, owner). (One-to-Many).
5.  **Building**: Towers or blocks within the project. (One-to-Many).
6.  **UnitType**: Configurations (e.g., 2BHK) and their areas/prices. (One-to-Many).
7.  **ProjectArtifact**: Represents any file associated with the project (Documents, Images, Plans, Certificates). Replaces/Expands `ProjectDocument`.
8.  **QuarterlyUpdate**: Periodic status updates.

## Physical Schema (PostgreSQL)

### New/Modified Tables

#### `projects` (Existing, Modified)
- **Add**: `scraped_at` (Timestamp), `data_quality_score` (Integer), `last_parsed_at` (Timestamp).
- **Keep**: `raw_data_json` (JSONB) for full audit trail.

#### `bank_accounts` (New)
- **Columns**: `id`, `project_id`, `bank_name`, `branch_name`, `account_number`, `ifsc_code`, `account_holder_name`.

#### `land_parcels` (New)
- **Columns**: `id`, `project_id`, `survey_number`, `area_sqmt`, `owner_name`, `encumbrance_details`.

#### `project_artifacts` (Refactor of `project_documents`)
- **Columns**:
    - `id`, `project_id`
    - `category` (e.g., 'legal', 'technical', 'promoter', 'media')
    - `artifact_type` (e.g., 'registration_certificate', 'building_plan', 'site_photo')
    - `file_path` (Relative path to storage)
    - `source_url` (Original URL)
    - `file_format` (pdf, jpg, etc.)
    - `is_preview` (Boolean, true if it was a 'Preview' link)

### Artifact Storage Strategy

We will move away from storing artifacts inside `runs/` for long-term retention.

1.  **Raw HTML**:
    - **Storage**: `data/archive/html/{state_code}/{registration_number}/{timestamp}.html`
    - **Purpose**: Re-parsing without re-crawling.

2.  **Artifacts (PDFs/Images)**:
    - **Storage**: `data/artifacts/{state_code}/{registration_number}/{artifact_type}_{hash}.{ext}`
    - **DB Reference**: `project_artifacts.file_path` stores relative path from `data/artifacts/`.

3.  **JSON**:
    - **Storage**: `data/archive/json/{state_code}/{registration_number}/{timestamp}.v1.json`
    - **DB Reference**: Content stored in `projects.raw_data_json`.

## Data Flow

1.  **Scraper**: Outputs to `runs/run_<id>/`.
2.  **Loader**:
    - Reads `runs/run_<id>/`.
    - Upserts `Project` and child tables.
    - **New**: Moves/Copies artifacts to `data/artifacts/` and updates `project_artifacts` table.
    - **New**: Archives HTML/JSON to `data/archive/`.
