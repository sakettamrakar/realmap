# Phase 4 Geocoding Design

This document captures the normalization strategy for producing a geocoding-ready
`normalized_address` for CG RERA projects.

## Source fields

Addresses are synthesized from data already stored in the database or preserved in
V1 JSON payloads:

- `projects.full_address` (project_details.project_address)
- `projects.village_or_locality`
- `projects.tehsil` (project_details.tehsil)
- `projects.district` (project_details.district)
- `projects.pincode` (if present in DB/JSON)
- `projects.state_code` (metadata.state_code) or explicit state name if captured
- Static country suffix: `India`

## Normalization rules

- Order: `address_line`, `village_or_locality`, `tehsil`, `district`, `state`,
  `pincode`, `country`.
- Skip any component that is `null`, empty, or only whitespace.
- Trim extra whitespace and convert stray commas to spaces before joining.
- Components are joined with `", "`.
- Abbreviation cleanup:
  - `Dist.`/`Dist` → prefixed as `District <name>` when found at the start.
  - `Tah.`/`Tahsil` → prefixed as `Tehsil <name>` when found at the start.
- State name is expanded from the state code when possible (`CG` → `Chhattisgarh`).
- Country defaults to `India`.

## Confidence heuristic

For downstream geocoding we record a coarse confidence flag:

- **Low confidence** when fewer than three components are present **or** when no
  district is available alongside any locality component (address line, village,
  or tehsil).
- Otherwise the address is considered sufficient for first-pass geocoding.

## Backfill process

The `tools/backfill_normalized_addresses.py` script populates missing
`normalized_address` values by:

1. Querying rows where `normalized_address` is `NULL` or empty.
2. Building an `AddressParts` structure using DB columns with fallbacks from
   `raw_data_json.project_details` and `raw_data_json.metadata` when present.
3. Formatting the address using the rules above.
4. Writing the formatted value back to the project row (or logging only when
   `--dry-run` is set).

### Running the script

```
python tools/backfill_normalized_addresses.py \
  --config config.example.yaml \
  --limit 100 \
  --dry-run
```

- Omit `--dry-run` to commit updates.
- Use `--limit` for safe sampling during development.

### Expected behavior with missing data

- If only state/country information exists, the normalized address will still be
  generated but marked as low confidence.
- Rows with no usable components are skipped and reported in the script stats.
# Phase 4 GEO Design

## Context and findings
- **Available V1 JSON samples:** The repository currently includes example V1 payloads under `outputs/` and `tests/qa/fixtures/`. Both carry location hints only in `project_details` and promoter address strings. Key fields visible are `project_address`, `district`, `tehsil`, and the state code in metadata; no latitude/longitude or pincode fields appear in these samples, and locality/village is absent as a discrete field. Additional addresses may show up inside `land_details.land_address` or promoter addresses but are secondary to the project location.【F:outputs/v1_scraper_json_schema_example.json†L2-L83】【F:tests/qa/fixtures/project_v1.json†L2-L42】
- **Run directories:** No `runs/run_*/scraped_json/` data ships in the repo, so the above samples are the best proxy for current address fidelity. Prior documentation notes that real runs normally live under `outputs/realcrawl/runs/run_*/scraped_json/` with filenames like `project_{state}_{reg_no}.v1.json`.【F:docs/DATA_INVENTORY.md†L1-L33】
- **DB schema today:** The `projects` table already stores `district`, `tehsil`, `village_or_locality`, `full_address`, `pincode`, `latitude`, `longitude`, `geocoding_status`, and `geocoding_source`, but only `full_address` and location hierarchy columns are populated by the loader; lat/lon are present but unused. No column captures the normalized geocoder input or a formatted geocoder response.【F:cg_rera_extractor/db/models.py†L13-L43】

## Current address reliability for geocoding
- **Consistently present:** `project_address`, `district`, `tehsil`, `metadata.state_code` ("CG" → Chhattisgarh) appear in every sample file.
- **Sometimes present:** Addresses inside `land_details` and `promoter_details.address` may add locality hints; pincode is not present in the samples and may need extraction from raw text if available in future runs.
- **Normalized input candidates:** For geocoding, we can safely build a string from available fields in this order when present: `project_address`, `village_or_locality` (if we later parse one), `tehsil`, `district`, `Chhattisgarh`, `pincode`, `India`. Even without pincode, the district+state pair should be reliable enough for locality-level matches.

## Proposed GEO fields for `projects`
| Column | Type | Purpose / Notes |
| --- | --- | --- |
| `latitude` | `Numeric(9,6)` (existing) | Store the resolved latitude as decimal degrees.
| `longitude` | `Numeric(9,6)` (existing) | Store the resolved longitude as decimal degrees.
| `geo_precision` | `String(32)` (new) | Categorical resolution of the coordinates: `exact` (rooftop/parcel), `street`, `locality`, `district`, `state`, `fallback` (only state inferred), `unknown`. Drives map zoom and distance confidence.
| `geo_source` | `String(64)` (rename and reuse existing `geocoding_source`) | Source of coordinates: `google`, `osm`, `mapbox`, `manual`, `imported`. Rename existing `geocoding_source` column to `geo_source` and expand allowed values to this set.
| `geo_status` | `String(64)` (rename and reuse existing `geocoding_status`) | Workflow status: `pending`, `geocoded`, `failed`, `needs_review`. Track retries and QA.
| `normalized_address` | `Text` (new) | String sent to the geocoder, assembled from structured fields with consistent ordering and separators; stored for reproducibility and debugging.
| `formatted_address` | `Text` (new, optional) | The cleaned, provider-returned address (e.g., Google formatted address) to display and audit.
| `geo_bbox` | `JSON` (optional/future) | Bounding box returned by provider when precision is coarse; useful for filters at district/locality level.

## Normalized address construction
1. Start with `project_details.project_address` as the anchor.
2. Append `village_or_locality` when/if we begin parsing it from raw data; otherwise skip.
3. Append `project_details.tehsil` and `project_details.district` if present.
4. Append literal `Chhattisgarh` (state name) derived from `metadata.state_code`.
5. Append `pincode` if captured or parsed.
6. Append `India` as the country suffix.
7. Join components with ", " and collapse duplicate/empty separators. Example: `"Plot 12, VIP Road, Raipur, Raipur, Chhattisgarh, 492001, India"` when pincode is known; otherwise omit it.

## GEO field usage rules
- **geo_precision assignment**
  - `exact`: Provider returns rooftop/parcel point or manual verification confirms precise entrance.
  - `street`: Provider returns street-level interpolation; bounding box optional.
  - `locality`: Only city/locality matched (e.g., district/tehsil centroid).
  - `district`: District-level centroid only.
  - `state`: State centroid fallback.
  - `fallback`: Only state-level centroid could be assigned (best-effort fallback).
  - `unknown`: No reliable match; lat/lon null.
- **geo_source values**: `google`, `osm`, `mapbox`, `manual`, `imported` (if supplied in source data). This replaces the existing `geocoding_source` column via rename.
- **geo_status lifecycle**: `pending` → `geocoded` (lat/lon present) or `failed` (no match) → optional `needs_review` after QA.

## JSON vs DB placement
- Geocoding outputs (`lat`, `lon`, `geo_precision`, `geo_source`, `geo_status`, `formatted_address`) should live in the DB only. The V1 JSON remains a raw scrape artifact; enriching it would create divergence between stored files and database truth.
- If we later export enriched JSON, include a small `geocoding` block mirroring the DB fields, but no change to the scraper output is required for Phase 4.

## Open questions / assumptions
- Pincode availability is uncertain; we may need to parse it from free-text addresses or future HTML fields.
- `village_or_locality` is unused in current JSON; confirming whether the site exposes a separate locality field would improve normalized addresses.
- Provider choice (Google vs OSM/Mapbox) will drive rate limits and accuracy; selection to be finalized with Ops.
- Column renames (`geocoding_source` → `geo_source`, `geocoding_status` → `geo_status`) should be applied via migration to maintain consistency.
