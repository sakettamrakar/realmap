# Data Model Migration Plan

This document outlines the steps to migrate from the current data model to the target model defined in `DATA_MODEL_TARGET.md`.

## Phase 1: Schema Updates (Non-Destructive)

1.  **Create New Tables**:
    - `bank_accounts`
    - `land_parcels`
    - `project_artifacts` (initially alongside `project_documents`)

2.  **Alter Existing Tables**:
    - Add `scraped_at`, `data_quality_score`, `last_parsed_at` to `projects`.

3.  **Migration Script**:
    - Generate Alembic revision or SQL script for the above changes.

## Phase 2: Loader Enhancement

1.  **Update `cg_rera_extractor/db/loader.py`**:
    - Add logic to parse `bank_details` from V1 JSON and insert into `bank_accounts`.
    - Add logic to parse `land_details` (if available) or extract from `raw_data` into `land_parcels`.
    - **Critical**: Add logic to map the `previews` section of V1 JSON to `project_artifacts`.
        - Iterate over `previews` dictionary.
        - Create `ProjectArtifact` record for each entry.
        - Use `notes` field as `source_url` or `file_path`.

## Phase 3: Backfill from Existing DB Data

Since `projects.raw_data_json` contains the full V1 JSON, we can backfill the new tables without re-crawling or re-reading files.

1.  **Create Backfill Script (`scripts/backfill_new_tables.py`)**:
    - Iterate over all `projects` in DB.
    - Read `raw_data_json`.
    - Parse `bank_details` -> Insert into `bank_accounts`.
    - Parse `previews` -> Insert into `project_artifacts`.
    - Parse `raw_data.unmapped_sections` -> Extract land details -> Insert into `land_parcels`.
    - Update `last_parsed_at` timestamp.

## Phase 4: Artifact Management (Optional but Recommended)

1.  **Artifact Mover Script**:
    - Scan `runs/` directories.
    - Identify preview files referenced in `project_artifacts`.
    - Move/Copy them to `data/artifacts/{state}/{reg_no}/`.
    - Update `project_artifacts.file_path` to the new canonical path.

## Phase 5: Cleanup

1.  **Deprecate `project_documents`**:
    - Once `project_artifacts` is verified, drop `project_documents` table.
2.  **Archive Runs**:
    - Move processed `runs/` to `data/archive/`.
