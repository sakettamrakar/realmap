# RealMap Airflow Orchestration

Apache Airflow integration for orchestrating the RealMap data pipeline.

## Quick Start

```powershell
cd c:\GIT\realmap\airflow
docker compose -f docker/docker-compose.yaml up -d
```

## Access

- **Airflow UI**: http://localhost:8080
- **Credentials**: `admin` / `admin`

## Main DAG: `realmap_etl`

Orchestrates the full ETL pipeline:

| Task Group | Tasks | Status |
|------------|-------|--------|
| pre_processing | config, browser_session, search_page, captcha_handling, listing_scraper, detail_html_fetcher, preview_capture | Placeholder (requires browser) |
| main_processing | raw_extractor, mapper_v1, qa_validator, normalization, **db_loader** | `db_loader` wired |
| post_processing | geocoding, amenity_stats, score_computation, ai_scoring, api_layer | Placeholder |

## Known Limitation: SQLAlchemy Version Conflict

⚠️ The realmap backend uses **SQLAlchemy 2.0** features (`Mapped[]`, `mapped_column()`), but Airflow 2.10.4 bundles SQLAlchemy 1.4.x. Installing SQLAlchemy 2.0 breaks Airflow's internal models.

### Current Workarounds

1. **BashOperator isolation**: Tasks use `BashOperator` to run Python code in subprocess
2. **External execution**: Run db_loader via external Python with SQLAlchemy 2.0:
   ```bash
   # From host machine with realmap's venv activated
   python -c "from cg_rera_extractor.db.loader import load_all_runs; load_all_runs('data/outputs/realcrawl/runs')"
   ```
3. **Wait for Airflow 3.0**: Expected to fully support SQLAlchemy 2.0

### Changes Made to Backend

Added backward-compatible Base class in `cg_rera_extractor/db/base.py`:
- Uses `DeclarativeBase` (SQLAlchemy 2.0) with fallback to `declarative_base()` (1.4)
- Sets `__allow_unmapped__ = True` for Airflow compatibility

## Architecture

```
realmap/
├── airflow/                    # Airflow orchestration (this folder)
│   ├── dags/                   # DAG definitions
│   ├── docker/                 # Docker Compose config
│   ├── logs/                   # Airflow logs
│   └── plugins/                # Custom operators/hooks
├── cg_rera_extractor/          # Backend (mounted at /opt/realmap)
└── ai/                         # AI modules (mounted at /opt/realmap)
```

## Stop Airflow

```powershell
docker compose -f docker/docker-compose.yaml down
```

## Reset Everything

```powershell
docker compose -f docker/docker-compose.yaml down -v
```
