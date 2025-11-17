# Test Playbook

## Phase 3 Quick Check
Use this short script to validate the Phase 3 pieces (DB wiring, loader, API) before running longer crawls.

1. Initialize the schema (uses `DATABASE_URL` or the URL from a provided config):
   - `python tools/init_db.py`
2. Load a single run of scraped V1 JSON into the database:
   - `python tools/load_runs_to_db.py --run-id <run_id>`
3. Start the FastAPI service locally:
   - `uvicorn cg_rera_extractor.api.app:app --reload`
4. Confirm the API is reachable and returning projects from the DB:
   - `curl http://localhost:8000/projects`

> Tip: For a fast sanity check without touching a real database, run `python tools/self_check.py` which now spins up an in-memory SQLite database, loads one V1 project, and verifies the API dependencies import correctly.
