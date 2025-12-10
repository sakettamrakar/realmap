# API Reference

This document summarizes the key HTTP endpoints exposed by the FastAPI application. For the complete design rationale and historical notes, see the legacy `PHASE6_API_DESIGN.md` and related documents.

## Base

- Protocol: HTTP/JSON
- Typical dev base URL: `http://localhost:8000`

## Health

### `GET /health`

- **Purpose**: Basic readiness check.
- **Response**: `{ "status": "ok" }` when the service is healthy.

## Projects

### `GET /projects`

- **Purpose**: List/search projects with basic filters.
- **Common query parameters** (subject to implementation):
  - `district`, `tehsil`
  - Score thresholds (e.g., `min_overall_score`)
  - Pagination (`page`, `page_size`)
- **Response**: Paginated list of project summaries.

### `GET /projects/{state_code}/{rera_registration_number}`

- **Purpose**: Fetch a single project by its natural key.
- **Path parameters**:
  - `state_code` – e.g., `CG`.
  - `rera_registration_number` – the RERA registration string.
- **Response**: A project detail object including RERA fields, geo fields, and, where available, scores and amenity summaries.

Other discovery and analyst-oriented endpoints may exist (e.g., for tags, verification, landmarks, and exports) and follow similar patterns. Inspect `cg_rera_extractor/api/routes_*.py` for the exact paths and schemas.

## Models

Pydantic schemas live under `cg_rera_extractor/api/schemas*.py` and describe:

- Project summary and detail payloads.
- Discovery entities (tags, verification, landmarks) when present.
- Auxiliary types such as pagination metadata.

The API is currently designed primarily for internal/trusted environments. Rate limiting middleware is in place to guard against accidental overload; auth can be tightened or extended as external use cases evolve.
