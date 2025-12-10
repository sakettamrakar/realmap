# Documentation Changes Summary

This file summarizes the restructuring of the `docs/` folder.

## New Structure

- `README.md`
- `Architecture.md`
- `Data-Pipeline.md`
- `Scraper-Engine.md`
- `Geo-Intelligence.md`
- `Amenities-Engine.md`
- `UI-UX-Design.md`
- `Deployment-Guide.md`
- `Debug-Runbook.md`
- `API-Reference.md`
- `Changelog.md`
- `Glossary.md`
- `Archived/` (for legacy docs)

## Merged/Referenced Files

- Developer workflows and architecture notes consolidated into `README.md`, `Architecture.md`, and `Scraper-Engine.md` (source: `DEV_GUIDE.md`).
- Geo design and pipeline docs referenced from `Geo-Intelligence.md` (sources: `GEO_PIPELINE.md`, `PHASE4_GEO_OVERVIEW.md`, `GEO_QA_PLAN.md`).
- Amenity and scoring docs referenced from `Amenities-Engine.md` (sources: `PHASE5_AMENITY_DESIGN.md`, `PHASE5_AMENITY_OVERVIEW.md`, `AMENITY_PROVIDER.md`, `AMENITY_STATS.md`, `PROJECT_SCORES.md`).
- API contracts summarized into `API-Reference.md` (source: `PHASE6_API_DESIGN.md`).

## Deleted Files

- None yet; legacy docs remain either in place or under `_archive/`/`Archived/` for now.

## Still Needs Human Review

- Verify that all legacy docs are either covered by, or safely referenced from, the new core files.
- Decide which phase-specific docs can be moved into `Archived/` versus kept as implementation references.
- Expand API reference once the external API surface stabilizes.
