# UI & UX Design

This document describes the frontend architecture and key user flows.

## Frontend Stack

- Framework: React + TypeScript
- Bundler: Vite
- Location: `frontend/`

## Key Screens

- **Home / Map + List**: Map of projects with filters and a synchronized list.
- **Project Detail**: RERA summary, geo context, amenities, and scores.
- **QA Tools**: Internal views for QA reports and debugging.

## Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

The app defaults to http://localhost:5173.

## Design Principles

- Clear separation between RERA (regulatory) and enrichment (geo/amenities).
- High-contrast, map-first exploration with summary cards.
- Explicit area/price labeling (carpet vs built-up vs super built-up).

See component-level docs and inline comments in `frontend/src` for implementation details.
