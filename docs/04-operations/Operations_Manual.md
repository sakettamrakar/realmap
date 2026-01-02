# Operations Manual

**Version:** 1.0.0
**Date:** 2025-12-12

---

## 1. Installation & Setup

### Prerequisites
*   **Python 3.10+**
*   **Node.js 18+**
*   **PostgreSQL 14+** (with PostGIS and pgvector)
*   **Tesseract OCR** (for PDF processing)
*   **Poppler** (for PDF to image conversion)

### Quick Start (Local)

1.  **Clone & Environment**
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    pip install -r requirements-pdf.txt  # PDF processing dependencies
    ```

2.  **Install System Dependencies (Windows)**
    ```powershell
    choco install tesseract
    choco install poppler
    ```

3.  **Database Init**
    ```powershell
    $env:DATABASE_URL = "postgresql+psycopg2://user:pass@localhost/realmap"
    python tools/init_db.py
    python tools/run_migrations.py
    ```

4.  **Frontend Setup**
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

### PDF Processing Issues
*   **Scenario:** `tesseract is not installed or it's not in your PATH`
*   **Fix:** Install Tesseract OCR:
    ```powershell
    choco install tesseract
    # Add to PATH: C:\Program Files\Tesseract-OCR
    ```

*   **Scenario:** `Unable to get page count. Is poppler installed?`
*   **Fix:** Install Poppler:
    ```powershell
    choco install poppler
    # Restart terminal after installation
    ```

*   **Scenario:** OCR returns empty or garbled text
*   **Fix:** Increase DPI and check language packs:
    ```powershell
    python tools/process_pdfs.py --page 1 --dpi 400
    ```

### AI Issues
*   **Scenario:** Smart Search returns 0 results.
*   **Fix:** Ensure `project_embeddings` table is populated. Run:
    ```powershell
    python -m ai.tools.generate_embeddings
    ```

*   **Scenario:** LLM extraction fails with "Model file not found"
*   **Fix:** Verify MODEL_PATH in `.env` points to a valid GGUF model file.

---

## 5. Monitoring & Maintenance
*   **Logs:** All services emit structured JSON logs to `stdout`.
*   **Backups:** Schedule nightly `pg_dump` of the `projects` table.
*   **Updates:** Run `pip install -r requirements.txt` after every `git pull`.

---

## 6. Related Documents
- [Architecture](../02-technical/Architecture.md)
- [Scraper Pipeline](../02-technical/Scraper_Pipeline.md)
- [PDF Processing](../02-technical/orchestration/pdf-processing.md)
- [AI Implementation](../03-ai/AI_Implementation.md)
