# Operations Manual

**Version:** 1.0.0
**Date:** 2025-12-12

---

## 1. Installation & Setup

### Prerequisites
*   **Python 3.10+**
*   **Node.js 18+**
*   **PostgreSQL 14+** (with PostGIS and pgvector)

### Quick Start (Local)

1.  **Clone & Environment**
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    ```

2.  **Database Init**
    ```powershell
    $env:DATABASE_URL = "postgresql+psycopg2://user:pass@localhost/realmap"
    python tools/init_db.py
    python tools/run_migrations.py
    ```

3.  **Frontend Setup**
    ```powershell
    cd frontend
    npm install
    ```

---

## 2. Running Services

### Backend API
```powershell
python -m cg_rera_extractor.api.main
# Listening on http://localhost:8000
```

### Frontend UI
```powershell
cd frontend
npm run dev
# Serving on http://localhost:5173
```

### AI Microservice
```powershell
uvicorn ai.main:app --port 8001
```

---

## 3. Deployment Guide

### Production Architecture
*   **API/UI:** Containerized (Docker).
*   **DB:** Managed Postgres (AWS RDS / Azure Postgres).
*   **Secrets:** Injected via Environment Variables (`DATABASE_URL`, `OPENAI_API_KEY`).

### Docker Compose (Simulated Prod)
```yaml
services:
  api:
    build: .
    command: uvicorn cg_rera_extractor.api.main:app --host 0.0.0.0
  db:
    image: postgis/postgis:14-3.3
```

---

## 4. Troubleshooting Runbook

### Scraper Issues
*   **Scenario:** Scraper halts on "Captcha Detected".
*   **Fix:** Ensure `headless: false` in `config.yaml` for manual intervention, or use a Captcha solving service.

### Database Issues
*   **Scenario:** `psycopg2.OperationalError`
*   **Fix:** Check if Postgres service is running. Verify `DATABASE_URL` credentials.

### AI Issues
*   **Scenario:** Smart Search returns 0 results.
*   **Fix:** Ensure `project_embeddings` table is populated. Run:
    ```powershell
    python -m ai.tools.generate_embeddings
    ```

---

## 5. Monitoring & Maintenance
*   **Logs:** All services emit structured JSON logs to `stdout`.
*   **Backups:** Schedule nightly `pg_dump` of the `projects` table.
*   **Updates:** Run `pip install -r requirements.txt` after every `git pull`.

---

## 6. Related Documents
- [Architecture](../02-technical/Architecture.md)
- [Scraper Pipeline](../02-technical/Scraper_Pipeline.md)
