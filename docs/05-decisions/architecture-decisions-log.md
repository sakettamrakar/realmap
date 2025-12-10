# Architecture Decisions Log

This document tracks notable architecture and system-level decisions. Historical gap analyses and implementation summaries under `docs/` and `docs/_archive/` serve as supporting material.

## Examples of recorded decisions

- Use a V1 JSON schema as the canonical scraper output and treat the database as a normalized projection of that schema.
- Maintain run-scoped artifacts (HTML, JSON, logs, QA) in a stable per-run directory layout for audit and reproducibility.
- Keep raw JSON payloads on the `projects` table for full-fidelity reprocessing when needed.
- Introduce separate geo, amenity, scoring, and discovery layers rather than mixing them into core project ingestion.
- Expose a read-only FastAPI surface backed by a dedicated read model (views/indexes) tuned for search and map use cases.

Use this file to briefly record additional decisions over time, referencing more detailed design docs where necessary.
