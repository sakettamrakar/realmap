# Duplicate Analysis Report - RealMap Production System

## Executive Summary
An investigation into the `realmapdb` production system has identified three distinct types of "duplicates" that affect data integrity and user experience. While the core `projects` table is protected by a unique constraint on RERA IDs, the system suffers from **logical duplication** (multiple RERA IDs for the same project name/address) and **process duplication** (repeated ingestion of the same records).

## 1. Duplicate Discovery Results

| Table | Uniqueness Candidate | Duplicate Count | Root Cause | Impact |
| :--- | :--- | :--- | :--- | :--- |
| `projects` | `(project_name, district, address)` | ~250 groups | Multiple RERA registrations for phases/blocks | Users see the same project multiple times in search results. |
| `promoters` | `promoter_name` | ~300 groups | Denormalized schema (1 promoter record per project) | Redundant data storage; difficult to aggregate developer-level stats. |
| `data_provenance` | `(project_id, run_id)` | ~5,000 rows | Idempotency failure in ingestion pipeline | Bloated audit logs; unnecessary DB writes on every scraper run. |
| `units` | `(project_id, unit_no)` | 0 | Unique constraint/Loader logic | No technical duplicates found within a single project. |

## 2. Root Cause Analysis

### A. Logical Duplication (Phases/Blocks)
The RERA system often issues separate registration numbers for different phases of the same project (e.g., 'METRO HEXA' has 29 registrations). 
- **Observation**: All 29 'METRO HEXA' records share the exact same address: `ST. XAVIER SCHOOL ROAD, NEAR SRISHTI PLAZO, LABHANDIH, RAIPUR`.
- **Current State**: The system treats these as 29 independent projects.

### B. Ingestion Idempotency Failure
The `loader.py` script correctly identifies existing projects by RERA ID but fails to prevent redundant processing.
- **Observation**: Project `PCGRERA250518000017` has **15 records** in `data_provenance`.
- **Mechanism**: Every time the scraper runs, it triggers `_load_project`, which:
  1. Updates the `Project` record.
  2. Deletes and re-inserts all child records (Promoters, Buildings, Units).
  3. Creates a new `DataProvenance` record.

### C. Denormalized Promoter Data
The `promoters` table is keyed to `project_id`. Even if the same promoter (e.g., 'MAHAVIR ASSOCIATES') manages 28 projects, the system creates 28 identical promoter records.

## 3. Data Drift Analysis
- **Projects**: Minimal drift. Most updates only refresh the `scraped_at` and `raw_data_json` fields.
- **Units/Buildings**: High churn. The "Delete-then-Insert" strategy causes ID instability for child records, breaking potential external foreign key references.

## 4. Affected Rows Summary
- **Total Projects**: ~300
- **Logical Duplicates**: ~250 (belonging to ~10 major project groups)
- **Redundant Provenance**: ~4,500 rows
- **Redundant Promoter Records**: ~800 rows

---
*Report generated on 2026-01-02 by Senior Database Architect.*
