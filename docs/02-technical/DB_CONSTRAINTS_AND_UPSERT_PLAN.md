# DB Constraints and Upsert Plan

This document details the technical changes required to enforce data uniqueness and implement idempotent write operations.

## 1. Database Constraints

### A. Projects Table
The existing `uq_projects_state_reg_number` is sufficient for RERA ID uniqueness. We will add:
- **Functional Index**: 
  ```sql
  CREATE UNIQUE INDEX idx_projects_normalized_rera 
  ON projects (state_code, LOWER(TRIM(rera_registration_number)));
  ```
- **Composite Uniqueness (Optional/Warning)**:
  A non-blocking unique index on `(project_name, district, full_address)` to flag potential duplicates for manual review.

### B. Promoters/Developers Table
- **New Table**: `developers`
- **Constraint**: `UNIQUE (normalized_name, city)`
- **Normalization**: `LOWER(TRIM(name))`

## 2. Data Normalization Rules

Before any INSERT or UPDATE, the following transformations must be applied:
1. **Strings**: `TRIM()` and `LOWER()` for all key fields (RERA ID, Project Name, Promoter Name).
2. **RERA ID**: Remove any non-alphanumeric characters except hyphens.
3. **Addresses**: Use the existing `normalize_address` utility to ensure consistency.

## 3. Upsert Strategy (PostgreSQL)

### A. Project Upsert
Refactor `loader.py` to use `ON CONFLICT`:

```sql
INSERT INTO projects (
    state_code, rera_registration_number, project_name, ...
) VALUES (
    :state, :rera, :name, ...
)
ON CONFLICT (state_code, rera_registration_number)
DO UPDATE SET
    project_name = EXCLUDED.project_name,
    status = EXCLUDED.status,
    scraped_at = EXCLUDED.scraped_at,
    raw_data_json = EXCLUDED.raw_data_json
WHERE projects.scraped_at < EXCLUDED.scraped_at;
```

### B. Child Table Idempotency
Instead of "Delete-then-Insert", use a "Delta Update" strategy:
1. Fetch existing child records.
2. Compare with new data.
3. `INSERT` new, `UPDATE` changed, `DELETE` missing.

## 4. Pipeline Safeguards

### A. API Layer
- Implement **Idempotency Keys** (UUID) for all POST requests.
- Validate RERA ID format using regex before hitting the DB.

### B. Ingestion Layer
- **Hash Check**: Before updating a project, compare the hash of the new `raw_data_json` with the existing one. If identical, skip the update and only update `last_checked_at`.

---
*Technical specification for Phase 3 & 4.*
