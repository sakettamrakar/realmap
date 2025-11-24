# GEO QA Plan

This document outlines lightweight quality checks to validate geocoding results using
only the database. The intent is to catch obvious issues (missing coordinates, values
outside India, address gaps) and provide quick samples for manual review.

## Metrics

- **Coverage of coordinates**: Percentage of projects where both latitude and longitude
  are present.
- **Missing latitude / longitude**: Raw counts of projects where either coordinate is
  `NULL` to understand which field is drifting.
- **Out-of-bounds coordinates**: Projects whose coordinates fall outside a plausible
  India bounding box (latitudes between **6.0–38.0**, longitudes between **68.0–98.0**).
- **Normalized address availability**: Projects lacking a usable address string. We
  treat `raw_data_json.normalized_address` as the primary source and fallback to
  `full_address` if the normalized field is absent.
- **Geocoding status distribution**: Count of projects by `geocoding_status` (treating
  `NULL` as `UNSET`) to surface stalled or failed geocoding.

## Sampling strategy

For each “bad” category, sample a handful of representative projects (ID, registration
number, name, district, coordinates) to make manual validation faster:

- Missing coordinates
- Coordinates outside the India bounding box
- Missing normalized address

## Reporting outputs

- **Console summary**: Human-readable metrics for quick inspection.
- **JSON report** (default: `runs/geo_qa_report.json`): Structured metrics plus the
  sampled projects, suitable for dashboards or historical comparisons.
