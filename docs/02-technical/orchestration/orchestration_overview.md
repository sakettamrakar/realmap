# 🎼 RealMap Orchestration

**Orchestration Analysis & Blueprint**

This section documents the complete orchestration flow of the RealMap platform, dividing the system into logical layers (`Pre-Processing`, `Main-Processing`, `Post-Processing`) and analyzing the execution graphs.

## 📚 Contents

1. **[Pre-Processing Layer](./preprocessing.md)**
   * Browser automation (Playwright)
   * CAPTCHA handling
   * Listing scraping & HTML acquisition
2. **[Main Processing Layer](./main_processing.md)**
   * Raw extraction & Schema mapping (V1 JSON)
   * QA Validation & Data Normalization
   * Database Loader
3. **[Post-Processing Layer](./post_processing.md)**
   * Geocoding & Amenity Enrichment
   * AI Scoring & Microservices
   * API Serving & Frontend
4. **[Dependency Graph](./dependency_graph.md)**
   * Module dependency visualization
   * Execution DAGs
5. **[Future Architecture](./future_architecture.md)**
   * Recommendations for moving to Airflow/Prefect
   * Proposed DAG designs
6. **[Unused Files Report](./unused_files.md)**
   * Audit of orphaned scripts and cleanup candidates

---

## 🏗️ High-Level Architecture

The RealMap pipeline operates as a sequence of localized transformations, currently orchestrated by `cg_rera_extractor/runs/orchestrator.py` but designed to be modular.

```mermaid
graph TD
    subgraph PRE[Pre-Processing]
        A[Config] --> B[Browser Session]
        B --> C[Search Page]
        C --> D[Listing Scraper]
        D --> E[Detail HTML Fetcher]
    end

    subgraph MAIN[Main Processing]
        E --> F[Raw Extractor]
        F --> G[Mapper V1]
        G --> H[QA Validator]
        H --> I[(PostgreSQL DB)]
    end

    subgraph POST[Post-Processing]
        I --> J[Geocoding]
        I --> K[Amenity Stats]
        J & K --> L[Score Computation]
        I --> M[AI Scoring]
        M --> N[API Layer]
    end

    PRE --> MAIN --> POST
```
