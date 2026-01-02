# Architecture Evolution: Project Deduplication & Multi-RERA Support

## 1. Current State (Before)
The system currently operates on a 1:1 mapping between a RERA Registration and a Project.

### Model
- **Table**: `projects`
- **Unique Identifier**: `rera_registration_number`
- **Assumption**: One RERA ID = One physical real estate project.

### Issues
- **Logical Duplicates**: Multi-phase projects (e.g., METRO HEXA) appear as 29 separate projects in the UI.
- **Data Redundancy**: Identical promoter and unit data are stored 29 times.
- **Broken Analytics**: Aggregations (e.g., "Total units in Raipur") are inflated by redundant records.

---

## 2. Target State (After)
We introduce a hierarchical model that separates the **Physical Project** from its **Legal Registrations (RERA IDs)**.

### New Model Structure
- **`parent_projects`**: Represents the physical project (e.g., "Overseas Palm Resorts").
- **`projects`**: Represents a specific RERA Registration/Phase (e.g., "Phase 1", "Block A").

### Diagram
```text
+-------------------+
|  parent_projects  |  <-- Physical Entity (Canonical Name, Address, Promoter)
+---------+---------+
          |
          | 1:N
          |
+---------v---------+
|     projects      |  <-- Legal Registration (RERA ID, Specific Phase Data)
+---------+---------+
          |
          +-----> promoters (1:N)
          +-----> buildings (1:N)
          +-----> unit_types (1:N)
          +-----> rera_filings (1:N)
```

---

## 3. Rationale
- **Backward Compatibility**: The `projects` table remains the primary data store for all extracted details. Existing foreign keys (to `buildings`, `unit_types`, etc.) do not need to be moved, minimizing risk.
- **Incremental Rollout**: We can add the `parent_project_id` and backfill it without stopping the system.
- **Search Optimization**: The UI can now group results by `parent_project_id` to show a single card for "Overseas Palm Resorts" with "28 Phases" listed inside.

---

## 4. Key Changes
1. **New Table**: `parent_projects` to store canonical project identity.
2. **New Column**: `projects.parent_project_id` to link registrations to their parent.
3. **Ingestion Logic**: Updated to perform "Parent Lookup" before "Registration Insert".
