# Geocoding pipeline and batch workflow

This repository supports geocoding projects using configurable providers and a
local cache to minimize repeated external lookups. The pipeline is designed to
work with the `normalized_address` stored for each project record and to backfill
coordinates plus associated metadata.

## Providers

Providers are configured under the top-level `geocoder` block in the YAML config
(see `config.example.yaml`). Two providers are available:

- **OpenStreetMap Nominatim** (default): No API key required, but subject to
  strict rate limits. Configure a custom `base_url` when pointing at a
  self-hosted instance.
- **Google Maps Geocoding API**: Requires an API key supplied via
  `geocoder.api_key`. Requests are throttled and retried on transient errors.

Key configuration options:

- `provider`: `nominatim` or `google`.
- `api_key`: Only needed for Google.
- `rate_limit_per_sec`: Maximum requests per second enforced client-side.
- `cache_path`: Location of the SQLite cache file.
- `request_timeout_sec`, `retries`, `backoff_factor`: Control HTTP timeout and
  retry behavior for transient failures.

## Cache

Geocoding responses are cached in a SQLite database (default:
`data/geocode_cache.sqlite`). Entries are keyed by `normalized_address` and
store latitude, longitude, formatted address, precision hints, provider source,
raw provider payload, and `last_updated_at`. The cache is checked before any
provider call and updated after successful lookups.

## Batch script

Run the batch geocoder via `tools/geocode_projects.py`.

Examples:

```bash
# Use config for DB + geocoder settings
python tools/geocode_projects.py --config ./config.example.yaml --limit 50

# Override provider from the CLI
python tools/geocode_projects.py --provider nominatim --limit 10

# Dry-run without persisting updates
python tools/geocode_projects.py --dry-run --limit 20
```

Behavior:

- Selects projects where `normalized_address` is present and `lat`/`lon` or
  `geo_source` is missing.
- Uses the configured geocoder (with caching) to resolve coordinates.
- On success, updates `lat`, `lon`, `formatted_address`, `geo_precision`,
  `geo_source`, and `geocoding_status` (plus legacy `geocoding_source`).
- Logs failures and continues, applying retries and exponential backoff on
  transient HTTP errors.

## Notes and limitations

- **Do not commit API keys**. Provide them via YAML or environment injection in
  runtime configuration only.
- Respect public provider rate limits. The client enforces a local throttle, but
  operators should set conservative values when using shared services.
- Cached results persist between runs; delete the cache file to force refreshes.
