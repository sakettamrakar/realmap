# API Reference

This document summarizes the public API surface. For full design notes, see `PHASE6_API_DESIGN.md`.

## Base URL

- Local: `http://localhost:8000`

## Health

- `GET /health` — returns `{ "status": "ok" }` when the API is ready.

## Project Search & Map

- `GET /projects`
  - Query params (subset):
    - `district`, `status`, `q` (name/registration substring)
    - `limit`, `offset`
  - Response: list of `ProjectSummary` objects.

- `GET /projects/{state_code}/{rera_registration_number}`
  - Path params: `state_code`, `rera_registration_number`
  - Response: `ProjectDetail` object with promoters, buildings, units, documents, and quarterly updates.

Additional endpoints for map/search/filter flows are documented in `PHASE6_API_DESIGN.md` and implemented in `cg_rera_extractor/api/routes_*.py`.

## Schemas

Pydantic models are defined under `cg_rera_extractor/api/schemas*.py`:

- `ProjectSummary`
- `ProjectDetail`
- Discovery and tag-related schemas

## Rate Limiting & Auth

- Internal API is currently designed for trusted use; `RateLimitMiddleware` enforces tiered rate limits.
- Future externalization can add API keys and stricter auth headers.

See the code in `cg_rera_extractor/api` for the exact request/response contracts.
