# Web App Usage

This guide explains how to use the React/Vite UI to explore CG RERA projects once the backend API is running.

## Accessing the app

- Start the API (typically on port 8000).
- Start the frontend dev server in `frontend/`:

```powershell
cd frontend
npm run dev
```

- Open the printed URL (usually `http://localhost:5173`).

## Main screens

### 1. Map + List (Home)

- A map of projects with pins colored or sized by score.
- A synchronized list of projects in a sidebar or panel.
- Basic filters such as district, minimum overall score, and text search.

Interactions:

- Hover or click a pin to highlight the corresponding list item.
- Select a project in the list to open its detail view.

### 2. Project Detail

The detail view surfaces:

- RERA summary (registration number, promoter, status, key dates).
- Location card with map and address.
- Amenities and, where available, scores and nearby context.
- Discovery signals such as tags and trust badges (if configured).

The exact layout evolves as components like price comparison, area labels, and transaction insights are introduced, but the core contract is that all data is sourced from the API.

## Filters and search

Common filters (backed by API query params):

- **Location** – district and tehsil.
- **Scores** – minimum overall/location/amenity score.
- **Project type / status** – basic project category or lifecycle.

When discovery and trust features are enabled, the UI also supports:

- **Tags** – selecting locality/investment tags for faceted search.
- **Verification** – filtering to RERA-verified projects only.

## Analyst workflows

Analysts typically:

1. Use the map/list to slice by district and score thresholds.
2. Drill into detailed pages for specific projects to inspect RERA fields, geo precision, and amenity coverage.
3. Cross-reference findings with exports or direct API calls documented in `../03-engineering/api-reference.md`.

For component-level structure or adding new views, see `../03-engineering/code-structure.md`. 