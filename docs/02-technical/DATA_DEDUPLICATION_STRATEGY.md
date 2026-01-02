# Data Deduplication Strategy

This document outlines the strategy for consolidating existing duplicates and preventing future occurrences in the RealMap system.

## 1. Canonical Record Selection

For logical duplicates (same project name/address but different RERA IDs), we will NOT merge them into a single `Project` record, as RERA IDs must remain distinct for legal compliance. Instead, we will introduce a **Parent Project** concept.

### Selection Rules:
- **Primary**: The record with the most recent `approved_date`.
- **Secondary**: The record with the highest `data_quality_score`.
- **Tie-breaker**: The record with the lowest `id` (oldest insertion).

## 2. Merge & Consolidation Rules

### A. Project Grouping
- Introduce a `parent_project_id` in the `projects` table.
- Group projects by `LOWER(TRIM(project_name))` and `LOWER(TRIM(full_address))`.
- Link all phases/blocks to the "Canonical" record.

### B. Promoter Normalization
- Move promoter data to a standalone `developers` table.
- Link `projects` to `developers` via `developer_id`.
- **Merge Rule**: Preserve the most complete contact info (Email/Phone) from the most recent project filing.

### C. Field Preservation
- **Preserve**: All unique RERA IDs, documents, and unit lists (they are phase-specific).
- **Aggregate**: Total units, total area, and price ranges at the Parent level.

## 3. Safe Cleanup Strategy

### A. Soft Delete
- Do NOT hard delete any `Project` records.
- Use a `is_active` or `superseded_by_id` flag for redundant `data_provenance` records.

### B. Archival
- Move `data_provenance` records older than 6 months to a `data_provenance_archive` table if they are not the "latest" for a given `run_id`.

### C. Audit Logging
- Every merge operation must be logged in a `deduplication_audit` table, recording:
  - `source_ids`
  - `target_id`
  - `timestamp`
  - `operator_id`

## 4. Implementation Roadmap

1. **Step 1**: Run grouping query to identify potential Parent-Child relationships.
2. **Step 2**: Create `developers` table and migrate promoter data.
3. **Step 3**: Update `loader.py` to check for existing `developer_name` before inserting.
4. **Step 4**: Implement the "Parent Project" linking logic in the API layer to group phases in search results.

---
*Strategy approved for Phase 2 implementation.*
