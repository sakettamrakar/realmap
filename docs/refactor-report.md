# Documentation Refactor Report

This report inventories all existing documentation files and proposes actions to migrate to the new unified structure under `docs/`.

> NOTE: This report is a plan only. No files have been moved, deleted, or rewritten yet.

## 1. Target Structure

Planned final layout:

- `docs/00-overview/product-overview.md`
- `docs/00-overview/architecture-summary.md`
- `docs/00-overview/glossary.md`
- `docs/01-getting-started/quickstart.md`
- `docs/01-getting-started/installation-setup.md`
- `docs/01-getting-started/environment-config.md`
- `docs/02-user-guide/web-app-usage.md`
- `docs/02-user-guide/mobile-ux-guide.md`
- `docs/02-user-guide/rera-features.md`
- `docs/03-engineering/system-architecture.md`
- `docs/03-engineering/code-structure.md`
- `docs/03-engineering/api-reference.md`
- `docs/03-engineering/data-models.md`
- `docs/04-operations/deployment-guide.md`
- `docs/04-operations/devops-pipeline.md`
- `docs/04-operations/monitoring-alerting.md`
- `docs/04-operations/troubleshooting-runbook.md`
- `docs/05-decisions/architecture-decisions-log.md`
- `docs/05-decisions/design-rationale.md`
- `docs/legacy/archived-docs-index.md`

## 2. Classification Legend

- **KEEP** – Content still accurate and will be migrated (possibly trimmed) into the new structure.
- **MERGE** – Overlaps with other docs; key content will be merged into a new target file.
- **REWRITE** – Concept is needed but the existing doc is too phase-specific or outdated; will rewrite fresh, using it only as a reference.
- **ARCHIVE** – Kept for historical context under `docs/legacy/` with a pointer to its replacement.
- **DELETE** – Redundant after migration (e.g., indices that only point to now-merged docs).

## 3. File-by-File Plan

### 3.1 Root-level docs

| Old Path | Action | New Location / Mapping | Notes |
|---------|--------|------------------------|-------|
| `README.md` | MERGE | `docs/00-overview/product-overview.md`, `docs/01-getting-started/quickstart.md` | Current repo README is accurate for crawler/QA/DB; high-signal quickstart and feature bullets will move into overview + quickstart. Root `README.md` will become a short pointer to the docs tree. |
| `AI_Instructions.md` | KEEP | `docs/03-engineering/code-structure.md` ("AI collaboration" section) and remain as root file | Still valid; core guidance will be summarized under engineering docs while keeping the root file for tools. |
| `mobile_ux_session_summary.md` | ARCHIVE | `docs/legacy/archived-docs-index.md` | Session log for mobile UX work; use as reference for `mobile-ux-guide.md` but not part of main docs. |
| `analysis_output.txt` / `analysis_result.txt` / `db_inspection.txt` / `orm_output.txt` | ARCHIVE | `docs/legacy/archived-docs-index.md` | Raw analysis logs; not user-facing. |

### 3.2 Frontend docs

| Old Path | Action | New Location / Mapping | Notes |
|---------|--------|------------------------|-------|
| `frontend/README.md` | MERGE | `docs/02-user-guide/web-app-usage.md`, `docs/03-engineering/code-structure.md` | Use run instructions and feature overview; avoid duplication of API details already in backend docs. |
| `frontend/mobile_ux_integration_summary.md` | ARCHIVE | `docs/02-user-guide/mobile-ux-guide.md` (as implementation notes) | Use as source for describing BottomNav, ComplianceProgress, and App.tsx split; keep original under legacy. |

### 3.3 Core new docs (created earlier in `docs/`)

These already align well with the desired structure and will mostly be **MERGED/RENAMED**.

| Old Path | Action | New Location / Mapping | Notes |
|---------|--------|------------------------|-------|
| `docs/README.md` | MERGE | `docs/00-overview/product-overview.md` | This is currently the best high-level overview; will be the primary source for the new product overview. |
| `docs/Architecture.md` | MERGE | `docs/00-overview/architecture-summary.md`, `docs/03-engineering/system-architecture.md` | Mermaid diagram and component breakdown go into architecture-summary; deeper code layout into system-architecture. |
| `docs/Data-Pipeline.md` | MERGE | `docs/03-engineering/system-architecture.md`, `docs/03-engineering/data-models.md` | Pipeline stages and commands feed system-architecture; references to tables and views feed data-models. |
| `docs/Scraper-Engine.md` | MERGE | `docs/03-engineering/code-structure.md` | Scraper modules, CLI usage, and configs will be integrated into code-structure and quickstart. |
| `docs/Geo-Intelligence.md` | MERGE | `docs/03-engineering/data-models.md`, `docs/04-operations/troubleshooting-runbook.md` | Geo tables and flows go into data-models; runbook bits into troubleshooting. |
| `docs/Amenities-Engine.md` | MERGE | `docs/03-engineering/data-models.md` | Amenity and scoring tables, flows, and commands go into data-models. |
| `docs/UI-UX-Design.md` | MERGE | `docs/02-user-guide/web-app-usage.md`, `docs/02-user-guide/mobile-ux-guide.md` | UX flows and screen descriptions will be split between general web usage and mobile UX. |
| `docs/Deployment-Guide.md` | KEEP | `docs/04-operations/deployment-guide.md` | Already close to the desired operations guide; may be lightly reorganized. |
| `docs/Debug-Runbook.md` | KEEP | `docs/04-operations/troubleshooting-runbook.md` | Directly becomes the troubleshooting runbook with minor edits. |
| `docs/API-Reference.md` | KEEP | `docs/03-engineering/api-reference.md` | Becomes the canonical API reference and will be expanded where needed. |
| `docs/Changelog.md` | ARCHIVE | `docs/legacy/archived-docs-index.md` | Internal changelog; optional to keep but outside the new tree. Reference from legacy index. |
| `docs/Glossary.md` | KEEP | `docs/00-overview/glossary.md` | Already matches the target; mostly a rename/move. |
| `docs/_changes_summary.md` | ARCHIVE | `docs/legacy/archived-docs-index.md` | Meta-doc about previous doc refactors; keep for traceability only. |

### 3.4 Existing core technical docs

| Old Path | Action | New Location / Mapping | Notes |
|---------|--------|------------------------|-------|
| `docs/DEV_GUIDE.md` | MERGE | `docs/03-engineering/system-architecture.md`, `docs/03-engineering/code-structure.md` | Architecture, workflows, and testing strategy are still accurate; content will be redistributed into system-architecture and code-structure. |
| `docs/QA_GUIDE.md` | MERGE | `docs/04-operations/monitoring-alerting.md`, `docs/04-operations/troubleshooting-runbook.md` | QA workflows and report reading feed monitoring + runbook. |
| `docs/DB_GUIDE.md` | MERGE | `docs/03-engineering/data-models.md`, `docs/04-operations/devops-pipeline.md` | Schema overview into data-models; CLI flow into devops-pipeline. |
| `docs/DATA_INVENTORY.md` | MERGE | `docs/03-engineering/data-models.md` | Inventory will be collapsed into concise tables for data-models. |
| `docs/DATA_MODEL_CURRENT.md` | MERGE | `docs/03-engineering/data-models.md` | V1 JSON sections still describe real output; merged and updated alongside code. |
| `docs/DATA_MODEL_TARGET.md` | MERGE | `docs/03-engineering/data-models.md` | Target schema and artifact strategy inform the data-models section; keep only what matches implemented models. |
| `docs/DATA_MODEL_MIGRATION_PLAN.md` | ARCHIVE | `docs/05-decisions/design-rationale.md` | Design reasoning for schema evolution; treat as decision rationale and keep under decisions. |
| `docs/DB_MODEL_CURRENT.md` | MERGE | `docs/03-engineering/data-models.md` | Will cross-check against `cg_rera_extractor/db/models.py` and keep only consistent portions. |

### 3.5 Geo, amenities, pricing, and analytics

| Old Path | Action | New Location / Mapping | Notes |
|---------|--------|------------------------|-------|
| `docs/GEO_PIPELINE.md` | MERGE | `docs/03-engineering/system-architecture.md`, `docs/04-operations/devops-pipeline.md` | Provider configs and cache behavior go into engineering; operator steps into devops-pipeline. |
| `docs/GEO_QA_PLAN.md` | MERGE | `docs/04-operations/monitoring-alerting.md`, `docs/04-operations/troubleshooting-runbook.md` | QA metrics and checks become monitoring + troubleshooting entries. |
| `docs/PHASE4_GEO_OVERVIEW.md` | MERGE | `docs/03-engineering/system-architecture.md` | End-to-end GEO overview becomes part of core geo section. |
| `docs/PHASE4_GEO_DESIGN.md` | ARCHIVE | `docs/05-decisions/design-rationale.md` | Detailed design/constraints kept as design rationale. |
| `docs/PHASE5_AMENITY_DESIGN.md` | ARCHIVE | `docs/05-decisions/design-rationale.md` | Amenity design doc treated as rationale. |
| `docs/PHASE5_AMENITY_OVERVIEW.md` | MERGE | `docs/03-engineering/data-models.md`, `docs/03-engineering/system-architecture.md` | Overview feeds amenity/scoring sections. |
| `docs/AMENITY_PROVIDER.md` | MERGE | `docs/03-engineering/system-architecture.md` | Provider details folded into amenity pipeline description. |
| `docs/AMENITY_STATS.md` | MERGE | `docs/03-engineering/data-models.md` | Stats tables and metrics merged into data-models. |
| `docs/PROJECT_SCORES.md` | MERGE | `docs/03-engineering/data-models.md` | Scoring schema and fields merged into data-models/read model description. |
| `docs/PHASE_PRICE_DESIGN.md` | ARCHIVE | `docs/05-decisions/design-rationale.md` | Conceptual price design; keep as decisions, ensure no unimplemented promises leak into main docs. |

### 3.6 API, discovery, and read model

| Old Path | Action | New Location / Mapping | Notes |
|---------|--------|------------------------|-------|
| `docs/API_GAP_ANALYSIS.md` | ARCHIVE | `docs/05-decisions/design-rationale.md` | Historical gaps; not needed for primary docs. |
| `docs/API_IMPLEMENTATION_SUMMARY.md` | MERGE | `docs/03-engineering/api-reference.md`, `docs/05-decisions/architecture-decisions-log.md` | Implementation-state notes merged into API reference and decisions log. |
| `docs/PHASE6_API_DESIGN.md` | MERGE | `docs/03-engineering/api-reference.md`, `docs/05-decisions/design-rationale.md` | Contract details still align with current FastAPI routes; design commentary goes into decisions. |
| `docs/PHASE6_READ_MODEL.md` | MERGE | `docs/03-engineering/data-models.md` | Read model and indexes merged into data-models with verification against models and migrations. |
| `docs/PHASE6_ANALYST_TOOLS.md` | MERGE | `docs/02-user-guide/web-app-usage.md`, `docs/03-engineering/api-reference.md` | Analyst CLI/API usage bridged into user guide and API reference. |
| `docs/DISCOVERY_GAP_ANALYSIS.md` | ARCHIVE | `docs/05-decisions/architecture-decisions-log.md` | Gap report predating now-complete discovery layer; tagged as historical. |
| `docs/DISCOVERY_IMPLEMENTATION.md` | MERGE | `docs/03-engineering/data-models.md`, `docs/03-engineering/api-reference.md` | Discovery DB models and endpoints consolidated into engineering docs. |

### 3.7 UX/Frontend phase docs

| Old Path | Action | New Location / Mapping | Notes |
|---------|--------|------------------------|-------|
| `docs/FRONTEND_GAP_ANALYSIS.md` | ARCHIVE | `docs/05-decisions/architecture-decisions-log.md` | Past gap analysis; already addressed by `FRONTEND_IMPLEMENTATION_SUMMARY.md`. |
| `docs/FRONTEND_IMPLEMENTATION_SUMMARY.md` | MERGE | `docs/02-user-guide/web-app-usage.md`, `docs/02-user-guide/mobile-ux-guide.md`, `docs/03-engineering/code-structure.md` | Component details power mobile-ux-guide and engineering view of UI. |
| `docs/ui_refactor_spec.md` | MERGE | `docs/05-decisions/design-rationale.md` | Specification of UI refactors; treated as rationale and future work. |

### 3.8 QA and project scoring

| Old Path | Action | New Location / Mapping | Notes |
|---------|--------|------------------------|-------|
| `docs/PHASE6_QA_CHECKLIST.md` | MERGE | `docs/04-operations/monitoring-alerting.md` | Checklist becomes an SRE-style checklist for QA and smoke tests. |
| `docs/QA_GUIDE.md` | (see above) |  | Already mapped; central to QA sections. |
| `docs/QA_GUIDE.md` + `docs/QA_GUIDE`-referenced tools | MERGE | `docs/04-operations/monitoring-alerting.md`, `docs/04-operations/troubleshooting-runbook.md` | Report reading and QA navigation integrated. |

### 3.9 Misc project docs

| Old Path | Action | New Location / Mapping | Notes |
|---------|--------|------------------------|-------|
| `docs/PROJECT_SCORES.md` | (see above) |  | Folded into data models/read model. |
| `docs/AMENITIES_VS_LOCATION.md` | MERGE | `docs/02-user-guide/rera-features.md`, `docs/03-engineering/data-models.md` | Conceptual explanation of amenities vs location used for feature docs and data modeling. |
| `docs/PHASE6_ANALYST_TOOLS.md` | (see above) |  | Bridges analyst workflows. |

### 3.10 Archived cluster under `docs/_archive`

All of these are already marked "ARCHIVED" in their first line and superseded by newer guides.

| Old Path (prefix `docs/_archive/`) | Action | New Location / Mapping | Notes |
|------------------------------------|--------|------------------------|-------|
| `DB_DEBUG_SESSION_COMPLETION.md`, `DB_DELIVERABLES.md`, `DB_PIPELINE_VERIFICATION.md`, `DB_QUICK_REFERENCE.md`, `DB_IMPLEMENTATION_SUMMARY.md`, `DB_LOADING_TEST_RESULTS.md`, `DB_DOCUMENTATION_INDEX.md` | DELETE (after migration) | Listed in `docs/legacy/archived-docs-index.md` | They all point to consolidated DB docs; we will keep a single brief entry in legacy index referencing `DB_GUIDE`. |
| `USER_GUIDE.md`, `REAL_CRAWL_GUIDE.md` | ARCHIVE | `docs/00-overview/product-overview.md`, `docs/01-getting-started/quickstart.md` | Their content is already in new docs; originals retained only via legacy index. |
| `QA_QUICK_START.md`, `QA_TESTING_GUIDE.md`, `QA_TESTING_INDEX.md`, `QA_TEST_SUITE_SUMMARY.md`, `QA_ARCHITECTURE_DIAGRAMS.md`, `QA_DELIVERY_SUMMARY.md`, `QA_FIX_PLAN.md` | DELETE (after confirming coverage) | `docs/04-operations/monitoring-alerting.md` | QA content is merged; we will preserve only a single legacy pointer. |
| `CLEANUP_QUICK_REFERENCE.md`, `CLEANUP_SUMMARY.md`, `CLEANUP_VERIFICATION.md`, `SESSION_SUMMARY_20251117.md` | ARCHIVE | `docs/legacy/archived-docs-index.md` | Historical session notes; not needed for main docs. |
| `PREVIEW_EXTRACTION_TEST_REPORT.md`, `PREVIEW_FIX_VERIFICATION.md` | ARCHIVE | `docs/04-operations/troubleshooting-runbook.md` (preview troubleshooting) | Keep as historical QA evidence; summarize relevance in runbook. |
| `LOGGING_AND_STATE_MANAGEMENT_IMPROVEMENTS.md`, `IMPLEMENTATION_SUMMARY.md`, `DEV_PLAN.md`, `PROJECT_STATUS.md` | ARCHIVE | `docs/05-decisions/architecture-decisions-log.md` | Design and status docs; used as input to decisions log and then archived. |
| `BROWSER_CLOSURE_FIX.md`, `CAPTCHA_BROWSER_FIXES.md` | ARCHIVE | `docs/04-operations/troubleshooting-runbook.md` | Tactical browser fixes integrated into troubleshooting; originals archived. |

## 4. Mapping to New Files

This section lists each new target file and its planned sources.

### 4.1 `docs/00-overview/product-overview.md`

**Sources:**
- `README.md`
- `docs/README.md`
- `frontend/README.md` (feature summary only)

**Scope:**
- High-level problem and solution statement.
- Bullet summary of key capabilities (crawl, QA, DB, geo, amenities, API, UI).
- Audience: investors, new engineers, non-technical stakeholders.

### 4.2 `docs/00-overview/architecture-summary.md`

**Sources:**
- `docs/Architecture.md`
- `docs/Data-Pipeline.md` (overview diagram)

**Scope:**
- One diagram + 1–2 pages of explanation across scraper, loaders, geo, amenities, API, frontend.

### 4.3 `docs/00-overview/glossary.md`

**Sources:**
- `docs/Glossary.md`

**Scope:**
- Direct rename/move; keep terms aligned with current code.

### 4.4 `docs/01-getting-started/quickstart.md`

**Sources:**
- `README.md` (quick setup + commands)
- `docs/Deployment-Guide.md` (first steps)
- `frontend/README.md` (minimal UI run instructions)

**Scope:**
- 10–15 minute path from clone to seeing data and UI.

### 4.5 `docs/01-getting-started/installation-setup.md`

**Sources:**
- `README.md`
- `docs/Deployment-Guide.md`

**Scope:**
- Python, Postgres, Node requirements; virtualenv; DB init; env vars.

### 4.6 `docs/01-getting-started/environment-config.md`

**Sources:**
- `docs/Scraper-Engine.md`
- `config.*.yaml` references

**Scope:**
- YAML config layout, env vars like `DATABASE_URL`, provider API keys.

### 4.7 `docs/02-user-guide/web-app-usage.md`

**Sources:**
- `docs/UI-UX-Design.md`
- `frontend/README.md`
- `docs/PHASE6_ANALYST_TOOLS.md` (analyst flows that surface via UI)

### 4.8 `docs/02-user-guide/mobile-ux-guide.md`

**Sources:**
- `mobile_ux_session_summary.md`
- `frontend/mobile_ux_integration_summary.md`
- Relevant portions of `docs/UI-UX-Design.md`

### 4.9 `docs/02-user-guide/rera-features.md`

**Sources:**
- `docs/AMENITIES_VS_LOCATION.md`
- `docs/PHASE6_ANALYST_TOOLS.md`

**Scope:**
- How RERA fields, geo, amenities, and scores surface in UI.

### 4.10 `docs/03-engineering/system-architecture.md`

**Sources:**
- `docs/Architecture.md`
- `docs/Data-Pipeline.md`
- `docs/GEO_PIPELINE.md`
- `docs/PHASE4_GEO_OVERVIEW.md`
- `docs/PHASE5_AMENITY_OVERVIEW.md`

### 4.11 `docs/03-engineering/code-structure.md`

**Sources:**
- `docs/DEV_GUIDE.md`
- `docs/Scraper-Engine.md`
- `frontend/README.md`
- `AI_Instructions.md`

### 4.12 `docs/03-engineering/api-reference.md`

**Sources:**
- `docs/API-Reference.md`
- `docs/PHASE6_API_DESIGN.md`
- `docs/API_IMPLEMENTATION_SUMMARY.md`

### 4.13 `docs/03-engineering/data-models.md`

**Sources:**
- `docs/DATA_MODEL_CURRENT.md`
- `docs/DATA_MODEL_TARGET.md`
- `docs/DATA_MODEL_MIGRATION_PLAN.md` (for context only)
- `docs/DB_MODEL_CURRENT.md`
- `docs/PHASE6_READ_MODEL.md`
- `docs/PROJECT_SCORES.md`
- `docs/Amenities-Engine.md`
- `docs/Geo-Intelligence.md`
- `docs/DISCOVERY_IMPLEMENTATION.md`

### 4.14 `docs/04-operations/deployment-guide.md`

**Sources:**
- `docs/Deployment-Guide.md`

### 4.15 `docs/04-operations/devops-pipeline.md`

**Sources:**
- `docs/Data-Pipeline.md`
- `docs/DB_GUIDE.md`
- `docs/GEO_PIPELINE.md`
- `docs/PHASE5_AMENITY_OVERVIEW.md`

### 4.16 `docs/04-operations/monitoring-alerting.md`

**Sources:**
- `docs/QA_GUIDE.md`
- `docs/GEO_QA_PLAN.md`
- `docs/PHASE6_QA_CHECKLIST.md`

### 4.17 `docs/04-operations/troubleshooting-runbook.md`

**Sources:**
- `docs/Debug-Runbook.md`
- `docs/PHASE4_GEO_OVERVIEW.md` (troubleshooting sections)
- `docs/PHASE5_AMENITY_OVERVIEW.md` (QA sections)
- `docs/_archive/*FIX*.md` (browser/CAPTCHA fixes)
- `docs/_archive/PREVIEW_*.md`

### 4.18 `docs/05-decisions/architecture-decisions-log.md`

**Sources:**
- `docs/API_IMPLEMENTATION_SUMMARY.md`
- `docs/DISCOVERY_GAP_ANALYSIS.md`
- `docs/FRONTEND_GAP_ANALYSIS.md`
- `docs/DOC_CLEANUP_PLAN.md`

### 4.19 `docs/05-decisions/design-rationale.md`

**Sources:**
- `docs/PHASE4_GEO_DESIGN.md`
- `docs/PHASE5_AMENITY_DESIGN.md`
- `docs/PHASE_PRICE_DESIGN.md`
- `docs/DATA_MODEL_MIGRATION_PLAN.md`
- `docs/ui_refactor_spec.md`

### 4.20 `docs/legacy/archived-docs-index.md`

**Sources:**
- `docs/_archive/*.md`
- Historical root and session docs (`mobile_ux_session_summary.md`, etc.)

**Scope:**
- A single index listing which historical docs were archived, what replaced them, and where they now live.

## 5. Code vs Docs Consistency Notes

- V1 JSON structure in `docs/DATA_MODEL_CURRENT.md` matches current parser outputs and DB loader behavior; will be revalidated against `cg_rera_extractor/parsing/*` and `cg_rera_extractor/db/loader.py` during rewrite.
- GEO pipeline docs (`GEO_PIPELINE.md`, `PHASE4_GEO_OVERVIEW.md`, `GEO_QA_PLAN.md`) align with the current `tools/backfill_normalized_addresses.py`, `tools/geocode_projects.py`, and `tools/check_geo_quality.py` scripts.
- Amenity and scoring docs (`PHASE5_AMENITY_OVERVIEW.md`, `AMENITY_PROVIDER.md`, `AMENITY_STATS.md`, `PROJECT_SCORES.md`) match the implemented models (`ProjectAmenityStats`, `ProjectScores`) and tools under `tools/`.
- API docs (`PHASE6_API_DESIGN.md`, `API-Reference.md`) broadly match the FastAPI routes implemented in `cg_rera_extractor/api/routes_*.py` and the read model in `PHASE6_READ_MODEL.md`, though final endpoint lists will be tightened to what actually exists in code.

## 6. Next Steps After Approval

Once you confirm this plan:

1. Create the new directory structure under `docs/`.
2. Rewrite/merge the new target files using only the sources listed above, ensuring all content matches the actual code.
3. Move historical/phase-specific docs into `docs/legacy/` and, where appropriate, delete redundant index/summary files after their content is incorporated.
4. Update root `README.md` to be a thin pointer into `docs/00-overview/product-overview.md` and `docs/01-getting-started/quickstart.md`.
5. Regenerate or hand-check internal links to ensure no broken references.
