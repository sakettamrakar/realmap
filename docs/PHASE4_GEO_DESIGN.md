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
