# Database Usage Analysis Report: `realmapdb`

**Date:** January 2, 2026  
**Role:** Senior Data Architect + Backend Analyst  
**Project:** RealMap (RERA Data Extraction & Analysis)

---

## 1. Summary
This report provides a comprehensive analysis of the PostgreSQL database `realmapdb`. The analysis covers schema introspection, application usage mapping, and recommendations for architectural improvements.

- **Total Tables:** 41
- **Actively Used:** 17
- **Partially Used / Empty Boilerplate:** 9
- **Unused / Orphaned (Enhancement Scaffolding):** 15

---

## 2. Table Inventory & Usage Classification

### 2.1 Actively Used Tables
These tables are core to the application, frequently updated by the scraper/loader, and queried by the AI services.

| Table Name | Row Count | Purpose | Usage Pattern |
| :--- | :--- | :--- | :--- |
| `projects` | 281 | Primary project records | Read/Write (Core Entity) |
| `project_locations` | 3,378 | Geocoding candidates and results | Read/Write (Mapping) |
| `project_documents` | 9,207 | Links to scraped PDF/HTML documents | Read/Write (Storage) |
| `project_amenity_stats` | 5,425 | Aggregated proximity amenity data | Read/Write (Analytics) |
| `document_extractions` | 3,357 | OCR/LLM extracted text from docs | Read/Write (AI/Search) |
| `data_provenance` | 700 | Audit trail for extraction runs | Write (Audit) |
| `amenity_poi` | 635 | Cached Points of Interest (Malls, etc.) | Read/Write (Cache) |
| `promoters` | 280 | Project promoter/owner details | Read/Write (Entity) |
| `bank_accounts` | 275 | RERA designated bank accounts | Read/Write (Financial) |
| `project_scores` | 155 | Computed lifestyle/connectivity scores | Read/Write (Scoring) |
| `ingestion_audits` | 83 | Scraper run metrics and HAR refs | Write (Ops) |
| `rera_filings` | 20 | Structured PDF extractions | Read/Write (AI) |
| `document_types` | 14 | Reference table for doc classification | Read (Reference) |
| `project_unit_types` | 7 | Canonical unit configurations | Read/Write (Specs) |
| `ai_scores` | 5 | AI-generated project quality scores | Read/Write (AI) |
| `project_imputations` | 1 | AI-predicted missing values | Read/Write (AI) |
| `alembic_version` | 1 | Database migration tracking | Read/Write (DevOps) |

### 2.2 Partially Used Tables
These tables have defined models and loader logic but are currently empty or have minimal data.

| Table Name | Row Count | Purpose | Status |
| :--- | :--- | :--- | :--- |
| `units` | 0 | Individual flat/plot inventory | Loader logic exists; needs population. |
| `buildings` | 0 | Tower/Block details | Scaffolding ready; needs extraction. |
| `unit_types` | 0 | Legacy unit mix table | Redundant with `project_unit_types`. |
| `quarterly_updates` | 0 | Construction progress tracking | Scaffolding ready; needs extraction. |
| `land_parcels` | 0 | Survey/Plot ownership data | Scaffolding ready; needs extraction. |
| `project_artifacts` | 0 | Media/Plan file tracking | Scaffolding ready; needs extraction. |
| `project_pricing_snapshots`| 0 | Historical price tracking | High value; needs data source. |
| `data_quality_flags` | 0 | Anomaly detection results | AI logic ready; needs execution. |
| `project_embeddings` | 0 | Vector data for semantic search | High value; needs embedding job. |

### 2.3 Unused / Orphaned Tables
These tables were created as part of "Enhancement Standards" (Points 1-26) but currently have no active loader logic or data.

| Table Name | Row Count | Purpose | Recommendation |
| :--- | :--- | :--- | :--- |
| `developers` | 0 | Entity-promoted promoters | Keep; use for cross-project trust scores. |
| `developer_projects` | 0 | Developer-Project association | Keep; supports JV/Partner tracking. |
| `project_possession_timelines`| 0 | Marketing vs RERA deadlines | High value for delay analysis. |
| `amenity_categories` | 0 | Structured amenity taxonomy | Keep; use to normalize onsite amenities. |
| `amenities` | 0 | Specific amenity definitions | Keep; part of taxonomy. |
| `amenity_types` | 0 | Amenity variants (e.g. Indoor Pool) | Keep; part of taxonomy. |
| `project_amenities` | 0 | Project-Amenity links | Keep; use for structured search. |
| `transaction_history` | 0 | Property registry records | High value; requires external data. |
| `tags` | 0 | Faceted search tags | Keep; use for SEO/Filtering. |
| `project_tags` | 0 | Project-Tag links | Keep; use for SEO/Filtering. |
| `rera_verifications` | 0 | Official portal verification logs | Keep; use for "Trust Badge" feature. |
| `landmarks` | 0 | Named entities (Malls, Parks) | Keep; use for Knowledge Graph. |
| `project_landmarks` | 0 | Project-Landmark proximity | Keep; use for Knowledge Graph. |
| `document_downloads` | 0 | Download queue tracking | Refactor; likely replaced by `ingestion_audits`. |

---

## 3. Data Value Assessment & Reuse Ideas

### 3.1 High-Value Opportunities
1.  **Granular Inventory (`units` + `buildings`):**
    - **Concept:** Move from "Project-level" to "Unit-level" search.
    - **Reuse:** Enable users to search for specific floors or available units. The `loader.py` already has a `_process_shredded_units` method that just needs to be triggered.
2.  **Semantic Search (`project_embeddings`):**
    - **Concept:** Power the AI Chat Assistant.
    - **Reuse:** Run a one-time job using `sentence-transformers` to populate this table from `document_extractions.raw_text`.
3.  **Market Validation (`transaction_history`):**
    - **Concept:** Compare RERA "Asking Price" vs Registry "Actual Price".
    - **Reuse:** If registry data (IGRS) can be obtained, this table becomes the most valuable asset for investors.

### 3.2 Consolidation Opportunities
- **`unit_types` vs `project_unit_types`:** These tables serve nearly identical purposes. `project_unit_types` is the newer, enhanced version. `unit_types` should be deprecated and merged into `project_unit_types`.
- **`document_downloads`:** This table seems redundant given that `ingestion_audits` and `project_documents` track the status and URLs of files.

---

## 4. Architecture Improvement Suggestions

### 4.1 Schema Normalization
- **Developer Promotion:** Currently, promoter names are strings in `promoters`. Migrating these to the `developers` table will allow for "Developer Profiles" and cross-project performance analysis (e.g., "Average delay for Developer X").
- **Locality Normalization:** The `projects` table has a `locality_id` pointing to an empty `localities` table. Populating `localities` will enable better faceted search and regional analytics.

### 4.2 Index Optimization
- **Unused Indexes:** Most tables have standard B-Tree indexes on foreign keys. As the dataset grows, consider **GIN indexes** on `jsonb` columns like `projects.qa_flags` and `document_extractions.extracted_metadata` for faster attribute filtering.
- **Spatial Indexes:** If `pgvector` is installed, `project_embeddings` should use an **HNSW index** for semantic search.

### 4.3 Naming Conventions
- The project uses a mix of `v1` (legacy) and `enhanced` (new) naming patterns. A unified naming convention (e.g., always using `project_` prefix for child tables) would improve developer experience.

---

## 5. Action Plan

1.  **Immediate (Next Sprint):**
    - Trigger the `units` and `buildings` extraction in `loader.py`.
    - Populate `project_embeddings` to enable AI Chat.
2.  **Short-Term (1 Month):**
    - Migrate `promoters` data to the `developers` entity model.
    - Populate `amenity_categories` and `tags` to enable faceted search in the frontend.
3.  **Long-Term:**
    - Integrate external registry data into `transaction_history`.
    - Implement the `rera_verifications` "Trust Badge" logic.

---
*End of Report*
