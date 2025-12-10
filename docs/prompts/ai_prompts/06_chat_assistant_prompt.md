# 06 Chat Assistant Prompt

## Role
AI Framework Engineer.

## Goal
Implement **AI Chat Assistant (Smart Query Engine)**. Allow natural language search ("3BHK near Whitefield under 1 cr") map to SQL/Vector queries.

## Inputs
- **User Query:** String.
- **Data:** `project_embeddings` (pgvector).

## Outputs
- **Code:** `cg_rera_extractor/ai/chat/engine.py`
- **API:** `POST /api/v1/chat/query`

## Constraints
- **Model:** Qwen2.5-7B-Instruct (local).
- **Latency:** < 3 seconds end-to-end.
- **Safety:** Read-only access to DB.

## Files to Modify
- `cg_rera_extractor/ai/chat/engine.py`
- `cg_rera_extractor/api/routes/chat.py`

## Tests to Run
- `pytest tests/integration/ai/test_chat.py`

## Acceptance Criteria
- [ ] Natural language query is converted to vector.
- [ ] Top 5 similar projects retrieved.
- [ ] LLM summarizes results into a coherent reply.
- [ ] Source citations (project names) included.

### Example Test
```bash
curl -X POST "http://localhost:8001/api/v1/chat/query" -d '{"q": "Cheap flats in Koramangala"}'
```
