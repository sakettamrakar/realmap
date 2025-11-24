# Amenity provider and cache

This module introduces an amenity provider abstraction (initially backed by the Overpass API) and a local cache to reuse fetched POIs across runs.

## Supported providers
- **OSM/Overpass** (default): uses `nwr` queries with curated tag mappings per normalized amenity type.
- **Google Places**: not yet implemented; selecting `amenities.provider: google` will raise a `NotImplementedError`.

## Configuration
New keys live under `amenities` in the YAML config (defaults are in `config.example.yaml`).

```yaml
amenities:
  provider: osm                 # Provider slug (osm/google)
  api_key: null                 # Only needed for commercial providers
  rate_limit_per_minute: 30     # Sleep-based rate limit
  request_timeout_sec: 15       # HTTP timeout for provider calls
  retries: 3                    # Retry attempts for transient failures
  backoff_factor: 1.5           # Exponential backoff multiplier
  search_radii_km:              # Default radii by amenity type
    school: [1, 3, 5]
    transit_stop: [1, 3, 5, 10]
    # ...
```

## Cache behaviour
- Cached in Postgres table `amenity_poi` keyed by `(provider, provider_place_id)`.
- Before hitting a provider, we read POIs with the same `amenity_type` that fall in the requested radius and are newer than the configured freshness window (default 60 days in the CLI tool).
- On cache miss the provider is queried, and results are upserted with refreshed `last_seen_at`.

### Table columns
- `provider`, `provider_place_id` (unique)
- `amenity_type`, `name`, `lat`, `lon`, `formatted_address`
- `source_raw` JSONB payload
- `last_seen_at`, `created_at`, `updated_at`

## Manual testing
Run migrations, then fetch a sample slice:

```bash
python tools/fetch_amenities_sample.py 21.2514 81.6296 school 3 --config config.example.yaml
```

The script prints total POIs and the closest names/distances. Re-running with the same parameters should serve from cache unless the freshness window expires.
