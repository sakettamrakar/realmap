# Documentation Status Report

**Date:** 2026-01-02
**Status:** Up-to-date

---

## 1. Summary of Changes

The documentation has been audited and updated to reflect the current codebase, specifically the implementation of the "Phase 0-3" enhancements (Intelligence, Discovery, and Trust layers).

### Updated Documents
*   **`docs/02-technical/Data_Model.md`**: Completely rewritten to match the split SQLAlchemy models (`models.py`, `models_enhanced.py`, `models_discovery.py`). Now includes `Locality`, `Tag`, `ProjectMedia`, `Developer`, etc.
*   **`docs/02-technical/Architecture.md`**: Updated to include the **Intelligence Layer** (AI Scoring, Price Trends) and **Discovery Layer** (Facets, Landmarks).
*   **`docs/02-technical/Scraper_Pipeline.md`**: Added post-processing steps for Locality Aggregation, Price Trends, and AI Scoring.
*   **`docs/02-technical/API_Reference.md`**: Added new endpoints: `/projects/search`, `/projects/{id}/media`, `/projects/{id}/inventory`, `/projects/lookup`.
*   **`docs/02-technical/orchestration/orchestration_overview.md`**: Updated to reflect Airflow integration.

### Deprecated Documents
The following documents are historical plans that have been implemented. They are marked as `[DEPRECATED]` in their headers:
*   `docs/02-technical/MIGRATION_PLAN.md`
*   `docs/02-technical/IMPLEMENTATION_PLAN.md`
*   `SCHEMA_GAP_ANALYSIS.md`

---

## 2. Code → Documentation Mapping

| Code Module | Primary Documentation |
|:---|:---|
| `cg_rera_extractor.db.models` | `docs/02-technical/Data_Model.md` (Core Domain) |
| `cg_rera_extractor.db.models_enhanced` | `docs/02-technical/Data_Model.md` (Enhanced Domain) |
| `cg_rera_extractor.db.models_discovery` | `docs/02-technical/Data_Model.md` (Discovery Domain) |
| `cg_rera_extractor.api` | `docs/02-technical/API_Reference.md` |
| `cg_rera_extractor.listing.scraper` | `docs/02-technical/Scraper_Pipeline.md` |
| `ai/` | `docs/03-ai/AI_Overview.md` |
| `airflow/` | `docs/02-technical/orchestration/orchestration_overview.md` |

---

## 3. Documentation Guidelines

### Do Not Touch (Historical/Generated)
*   `TECHNICAL_SPECIFICATION.md`: This is the original spec for the current implementation. Keep as reference.
*   `LLM_PROCESSING_STATUS.md`: Likely an automated status log.

### Maintenance
*   **Data Model**: When adding new tables, update `docs/02-technical/Data_Model.md`.
*   **API**: When adding endpoints, update `docs/02-technical/API_Reference.md`.
*   **Pipeline**: When changing the scraper or ETL flow, update `docs/02-technical/Scraper_Pipeline.md`.
