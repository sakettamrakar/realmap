# AI Implementation Runbook (Phase A-D)

## Overview
The "AI Path" is a separate, optional, deterministic pipeline consisting of:
- **`ai/` Microservice**: FastAPI server.
- **`ai_scores` Table**: Immutable store of AI results.
- **`ai/llm/adapter.py`**: Model agnostic adapter.

## Setup
1. **Environment**:
   Ensure `.env` has:
   ```ini
   AI_ENABLED=true
   MODEL_PATH=/path/to/model.gguf
   ```
2. **Database**:
   Run V002 migration:
   ```bash
   python migrations/apply_V002.py
   ```

## Running the Service
Start the service alongside or separately from the main app:
```bash
uvicorn ai.main:app --host 0.0.0.0 --port 8001
```

## Usage
### Score a Project
```http
POST /ai/score/project/{id}
```
**Effect**:
- Reads project data.
- Generates features.
- Calls LLM.
- Inserts row into `ai_scores`.
- Updates `projects.latest_ai_score_id`.

## Troubleshooting
- **Service Disabled**: Check `AI_ENABLED=false` in environment.
- **Mock Results**: If `MODEL_PATH` is invalid, the adapter returns mock data (check logs).
- **Hanging**: Default timeout is 60s. Adjust `LLM_TIMEOUT_SEC`.
- **Logs**: Check standard output for "DTO-LOG" or "ai.llm" logs.
