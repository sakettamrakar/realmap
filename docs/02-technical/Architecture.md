# System Architecture

**Version:** 1.0.0
**Date:** 2025-12-12

---

## 1. High-Level Overview

RealMap uses a modern ETL (Extract-Transform-Load) pipeline feeding into a high-performance web application.

```mermaid
flowchart LR
    A[RERA Portal] -->|Scraper| B(Raw HTML/JSON)
    B -->|Loader| C[(PostgreSQL DB)]
    C -->|Geo Pipeline| D[Enriched Projects]
    C -->|Amenity Pipeline| D
    D -->|FastAPI| E[API Layer]
    E -->|React| F[User Interface]
```

### Core Components
1.  **Scraper Engine:** Playwright-based crawler that navigates the CG RERA portal, extracting listings and PDF documents. Supports "Delta Mode" to only scrape new projects.
2.  **Database:** PostgreSQL 14+ acting as the central truth. Stores raw payloads, normalized relations, and geospatial data (PostGIS).
3.  **Enrichment Pipelines:**
    *   **Geo:** Normalizes addresses and fetches Lat/Lon via Nominatim/Google.
    *   **Amenities:** Aggregates nearby POIs (schools, hospitals) and computes "Quality Scores".
    *   **AI:** Vectorizes project descriptions for semantic search.
4.  **API Gateway:** A FastAPI Service offering REST endpoints for the frontend.
5.  **Frontend:** A React+Vite Single Page Application (SPA) utilizing Leaflet for maps.

---

## 2. Directory Structure

| Path | Purpose |
| :--- | :--- |
| `cg_rera_extractor/browser/` | Playwright session management & CAPTCHA handling. |
| `cg_rera_extractor/parsing/` | Logic to map Raw HTML -> V1 JSON Schema. |
| `cg_rera_extractor/db/` | SQLAlchemy models and Alembic migrations. |
| `cg_rera_extractor/api/` | FastAPI routes, schemas, and service layer. |
| `frontend/src/` | React source code (Components, Hooks, Pages). |
| `tools/` | CLI scripts for ETL, QA, and Analysis. |

---

## 3. Data Flow

1.  **Ingest:** `python -m cg_rera_extractor.cli` runs the scraper. Artifacts saved to `runs/`.
2.  **Load:** `loader.load_run_into_db` inserts data into `projects` table.
3.  **Backfill:** `geocode_projects.py` and `compute_project_scores.py` enrich the data.
4.  **Serve:** API reads from `projects` and `project_scores` tables to serve the UI.

---

## 4. Environment Strategy

*   **Local:** Dockerized DB, local Python venv, local Node server.
*   **Production:** Containerized services (API, UI, DB) orchestrated via Docker Compose or K8s.

---

## 5. Related Documents
- [Data Model](./Data_Model.md)
- [Scraper Pipeline](./Scraper_Pipeline.md)
- [API Reference](./API_Reference.md)
- [Orchestration Reference](./orchestration/orchestration_overview.md)
