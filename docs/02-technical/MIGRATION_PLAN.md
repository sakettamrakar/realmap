# Migration Plan: Zero-Downtime Deduplication

## Phase 1: Schema Expansion (Non-Breaking)
1. **Deploy Schema**: Run the SQL to create `parent_projects` and add `parent_project_id` to `projects`.
2. **Update Models**: Update SQLAlchemy models in `cg_rera_extractor/db/models.py` to include the new table and relationship.

## Phase 2: Data Backfill (Safe)
1. **Identify Parents**: Run a script to group existing `projects` by `(project_name, full_address, promoter_name)`.
2. **Populate Parents**: Insert unique groups into `parent_projects`.
3. **Link Children**: Update `projects.parent_project_id` for all existing records.
4. **Validation**: Verify that every project has a parent and that the grouping matches expectations.

## Phase 3: Ingestion Logic Update (Dual-Write/Lookup)
1. **Update Ingestion**: Modify the pipeline (`cg_rera_extractor/worker.py` or equivalent) to:
    - Extract RERA ID, Name, Address, Promoter.
    - **Step A**: Lookup/Create `parent_projects` record.
    - **Step B**: Insert/Update `projects` record with the `parent_project_id`.
2. **Idempotency**: Ensure the UPSERT logic on `projects` remains intact.

## Phase 4: Read-Path Optimization
1. **API Updates**: Update search and detail APIs to optionally group by `parent_project_id`.
2. **UI Updates**: Modify the frontend to display "Project Cards" based on `parent_projects` rather than individual RERA registrations.

## Phase 5: Constraint Enforcement
1. **Set NOT NULL**: Once backfill is 100% complete, set `projects.parent_project_id` to `NOT NULL`.
2. **Final Cleanup**: (Optional) Merge identical child data if needed, though keeping them as "Phases" is safer.

---

## Rollback Strategy
- **Reversible**: The `parent_project_id` column is nullable. If the new logic fails, the system can continue using the `projects` table as before.
- **Data Preservation**: No data is deleted. Even if a parent record is incorrect, the original RERA data in `projects` remains untouched.
