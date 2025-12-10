# 01 Feature Score Prompt

## Role
Senior Python ML Engineer & Backend Developer.

## Goal
Implement the **AI-powered Project Quality Score** engine. This system assigns a 0-100 score to real estate projects based on amenities, location, developer reputation, and legal status.

## Inputs
- **Files:** `cg_rera_extractor/db/models.py`, `cg_rera_extractor/db/loader.py`
- **Database:**
    - `projects` table (Columns: `amenity_list`, `latitude`, `longitude`)
    - `developers` table (Columns: `past_projects_count`, `legal_cases`)
- **Environment:** `MODEL_PATH` (for reasoning engine), `PG_DB_URL`

## Outputs
- **Code:**
    - `cg_rera_extractor/ai/scoring/quality_engine.py` (Core Logic)
    - `cg_rera_extractor/api/routes/scoring.py` (API Endpoint)
- **Database:**
    - Table: `project_ai_scores` (Schema: `id`, `project_id`, `total_score`, `sub_scores` (JSON), `explanation`, `model_version`, `created_at`)
- **API:** `POST /api/v1/score/project/{project_id}`

## Constraints
- **Resource Limits:** Optimize for local execution (latency < 2s).
- **Safety:** Do NOT modify the raw `projects` table directly; write only to `project_ai_scores`.
- **Idempotency:** Re-scoring the same project should update the existing score record or create a new versioned entry.

## Files to Modify
- `cg_rera_extractor/db/models.py` (Add `ProjectAIScore` model)
- `cg_rera_extractor/ai/scoring/quality_engine.py` (New file)
- `cg_rera_extractor/api/app.py` (Register router)

## Tests to Run
- Unit: `pytest tests/unit/ai/test_quality_engine.py` (Mock the LLM response)
- Integration: Curl command to score a sample project.

## Acceptance Criteria
- [ ] `project_ai_scores` table exists in DB.
- [ ] API endpoint accepts `project_id`.
- [ ] Scoring logic normalizes amenity count (0-1) and calculates weighted average.
- [ ] LLM generates a valid 1-sentence explanation.
- [ ] Response JSON includes `{ "score": 85, "reason": "...", "breakdown": {...} }`.

### Example Test (Curl)
```bash
curl -X POST "http://localhost:8001/api/v1/score/project/test-uuid"
# Expect:
# {
#   "project_id": "test-uuid",
#   "score": 78,
#   "explanation": "High amenity count but moderate location score.",
#   "model_version": "v1"
# }
```
