# Current Database Model

## Overview
The database schema is implemented in PostgreSQL using SQLAlchemy ORM. It consists of a central `projects` table and several child tables.

## Tables

### 1. `projects`
- **Primary Key**: `id` (Integer).
- **Natural Key**: `state_code` + `rera_registration_number` (Unique Constraint).
- **Columns**:
    - `project_name`, `status`, `district`, `tehsil`, `village_or_locality`, `full_address`.
    - `pincode`, `latitude`, `longitude` (Geocoding fields).
    - `approved_date`, `proposed_end_date`, `extended_end_date`.
    - `raw_data_json` (JSON): Stores the entire V1 JSON blob.
- **Relationships**: One-to-many with all other tables.

### 2. `promoters`
- **Columns**: `promoter_name`, `promoter_type`, `email`, `phone`, `address`, `website`.
- **Foreign Key**: `project_id`.

### 3. `buildings`
- **Columns**: `building_name`, `building_type`, `number_of_floors`, `total_units`, `status`.
- **Foreign Key**: `project_id`.

### 4. `unit_types`
- **Columns**: `type_name`, `carpet_area_sqmt`, `saleable_area_sqmt`, `total_units`, `sale_price`.
- **Foreign Key**: `project_id`.

### 5. `project_documents`
- **Columns**: `doc_type`, `description`, `url`.
- **Foreign Key**: `project_id`.
- **Issue**: Currently empty in the database, as the loader expects `v1_project.documents` to be populated, but the scraper puts document info in `previews`.

### 6. `quarterly_updates`
- **Columns**: `quarter`, `update_date`, `status`, `summary`, `raw_data_json`.
- **Foreign Key**: `project_id`.

## Mapping & Loader Logic
- **Upsert**: Projects are upserted based on `state_code` + `rera_registration_number`.
- **Child Entities**: Child records (promoters, buildings, etc.) are **deleted and re-inserted** on every load.
- **Raw Data**: The full V1 JSON is saved into `projects.raw_data_json`.

## Identified Issues
1.  **Missing Tables**:
    - `bank_details` are present in JSON but have no corresponding table.
    - `land_details` are present in JSON (sometimes) but have no table.
2.  **Data Gaps**:
    - `project_documents` table is empty because the loader doesn't map the `previews` section of the JSON.
    - `buildings` and `unit_types` are often empty in the DB because they are empty in the JSON lists, even if data exists in `raw_data`.
3.  **Redundancy**: `raw_data_json` column duplicates the structured data stored in other columns. This is acceptable for audit/backup but increases storage size.
4.  **Normalization**:
    - `district` and `tehsil` are stored as strings.
    - `status` is a string (no enum).
