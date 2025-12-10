# Developer Runbook: AI Microservice

**Role:** DevOps / AI Engineer  
**Scope:** Local Development & Debugging

---

## A. Pre-requisites
*   **OS:** Windows 10/11 (WSL2 recommended) or Linux.
*   **Docker:** Docker Desktop installed & running.
*   **Python:** 3.10+.
*   **Git:** Installed.
*   **Hardware:** 6GB+ VRAM GPU (Optional but recommended).

## B. Setup
1.  **Clone Repository:**
    ```bash
    git clone https://github.com/sakettamrakar/realmap.git
    cd realmap
    ```
2.  **Virtual Environment:**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```
3.  **Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Environment Variables:**
    ```bash
    cp .env.example .env
    # Edit .env and set database credentials and MODEL_PATH
    ```

## C. Database Setup (Docker)
Start the infrastructure services:
```bash
docker-compose -f docker/docker-compose.ai.yml up -d postgres redis
```
*   **Postgres Port:** 5432
*   **Redis Port:** 6379

## D. Migrations
Apply database schema changes:
```bash
# Assuming alembic
alembic upgrade head
```

## E. Running AI Service Locally
Start the FastAPI server:
```bash
uvicorn cg_rera_extractor.api.app:app --reload --host 0.0.0.0 --port 8001
```
*   Swagger UI: `http://localhost:8001/docs`

## F. Running a Single Test Job
Test the scoring endpoint manually:
```bash
curl -X POST "http://localhost:8001/api/v1/score/project" \
     -H "Content-Type: application/json" \
     -d '{"project_id": "123e4567-e89b-12d3-a456-426614174000"}'
```
*   **Expected Output:** JSON with `task_id` or `score` result.

## G. Running Batch Jobs
Enqueue a background task:
```bash
python scripts/queue_score.py --project_id "all" --batch_size 10
```

## H. Tests
1.  **Unit Tests (Fast):**
    ```bash
    pytest tests/unit -k quality_score
    ```
2.  **Integration Tests (Slow):**
    ```bash
    pytest tests/integration
    ```

## I. Debugging Runbook
*   **Logs:**
    ```bash
    docker-compose -f docker/docker-compose.ai.yml logs -f ai_service
    ```
*   **Inspect DB:**
    ```bash
    docker exec -it realmap_postgres psql -U user -d realmap_db
    # SQL: SELECT * FROM project_ai_scores ORDER BY created_at DESC LIMIT 5;
    ```
*   **Common Errors:**
    *   `CUDA OOM`: Reduce `n_gpu_layers` or restart python process.
    *   `Connection Refused`: Check if Docker container is up (`docker ps`).

## J. Checklist Before Merge
- [ ] Code is formatted (`black .`) and linted (`flake8`).
- [ ] Unit tests pass locally.
- [ ] Integration tests pass locally.
- [ ] Documentation updated (if API changed).
- [ ] New migration script created (if DB changed).
- [ ] Smoke tested one real project score.

## K. Release Steps
1.  Bump version in `pyproject.toml` / `VERSION`.
2.  Tag commit: `git tag -a v1.2.0 -m "Added Feature X"`.
3.  Push: `git push origin v1.2.0`.
4.  Run migrations in Staging.
5.  Deploy & Monitor logs.
