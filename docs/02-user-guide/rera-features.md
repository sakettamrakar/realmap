# RERA Features in the UI

This document explains how RERA-origin fields and enrichment layers surface in the product.

## RERA core fields

The UI exposes key RERA fields on the project detail page:

- Registration number and project name.
- Promoter details.
- Project status and important dates (approval, proposed/extended completion).
- Address and administrative fields (district, tehsil, locality).

These map directly to the normalized `projects` table and associated promoter tables in the database.

## Geo and location context

Geo enrichment adds:

- Normalized address and geocoded coordinates.
- A map pin on the project detail view.
- Quality indicators such as precision/source and, where relevant, QA notes.

The map/list screens use these coordinates for search and discovery, and geo QA ensures coverage remains within expected bounds.

## Amenities and scores

Where amenity and scoring pipelines have been run, the UI can surface:

- On-site amenity categories (e.g., clubhouse, parking, gym).
- Nearby amenity summaries (schools, hospitals, transit, etc.).
- Composite scores that summarize location and amenity quality.

These values are computed from amenity POIs and aggregated statistics stored in dedicated tables and exposed via the API.

## Discovery and trust

When discovery and trust features are enabled, additional signals appear:

- **Tags** – concise labels such as "metro-connected" or "near-it-park" to aid faceted search.
- **RERA verification badges** – status of verification against the official CG RERA portal, with optional links.
- **Landmarks** – curated landmarks associated with a project, surfaced as links or badges.

These are backed by dedicated discovery tables and endpoints; see `../03-engineering/data-models.md` and `../03-engineering/api-reference.md` for details.

The guiding principle is that the UI remains honest to the source RERA data while clearly distinguishing between raw regulatory fields and enrichment layers (geo, amenities, scores, discovery). 