"""Provider-backed geocoding with local caching and rate limiting."""

from __future__ import annotations

import logging
import sqlite3
import time
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import requests

from cg_rera_extractor.config.models import GeocoderConfig, GeocoderProvider

logger = logging.getLogger(__name__)


@dataclass
class GeocodeResult:
    """Normalized geocoding output."""

    lat: float
    lon: float
    formatted_address: str | None
    geo_precision: str | None
    geo_source: str
    raw: dict[str, Any] | None = None


class RateLimiter:
    """Simple rate limiter using sleep-based throttling."""

    def __init__(self, requests_per_second: float):
        self.min_interval = 1.0 / requests_per_second if requests_per_second > 0 else 0
        self._last_request_at = 0.0

    def wait(self) -> None:
        if not self.min_interval:
            return

        now = time.monotonic()
        elapsed = now - self._last_request_at
        remaining = self.min_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_request_at = time.monotonic()


class GeocodeCache:
    """SQLite-backed cache for geocoding responses."""

    def __init__(self, cache_path: str | Path):
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS geocode_cache (
                    normalized_address TEXT PRIMARY KEY,
                    lat REAL,
                    lon REAL,
                    formatted_address TEXT,
                    geo_precision TEXT,
                    geo_source TEXT,
                    raw_response TEXT,
                    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def fetch(self, normalized_address: str) -> GeocodeResult | None:
        with sqlite3.connect(self.cache_path) as conn:
            cursor = conn.execute(
                """
                SELECT lat, lon, formatted_address, geo_precision, geo_source, raw_response
                FROM geocode_cache
                WHERE normalized_address = ?
                """,
                (normalized_address,),
            )
            row = cursor.fetchone()
            if not row:
                return None

        lat, lon, formatted_address, geo_precision, geo_source, raw_response = row
        raw = None
        if raw_response:
            try:
                raw = json.loads(raw_response)
            except ValueError:
                raw = None
        logger.debug("Cache hit for '%s'", normalized_address)
        return GeocodeResult(
            lat=float(lat),
            lon=float(lon),
            formatted_address=formatted_address,
            geo_precision=geo_precision,
            geo_source=geo_source,
            raw=raw,
        )

    def store(self, normalized_address: str, result: GeocodeResult) -> None:
        raw_payload = json.dumps(result.raw) if result.raw is not None else None
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute(
                """
                INSERT INTO geocode_cache (
                    normalized_address, lat, lon, formatted_address, geo_precision, geo_source, raw_response, last_updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(normalized_address) DO UPDATE SET
                    lat=excluded.lat,
                    lon=excluded.lon,
                    formatted_address=excluded.formatted_address,
                    geo_precision=excluded.geo_precision,
                    geo_source=excluded.geo_source,
                    raw_response=excluded.raw_response,
                    last_updated_at=CURRENT_TIMESTAMP
                """,
                (
                    normalized_address,
                    result.lat,
                    result.lon,
                    result.formatted_address,
                    result.geo_precision,
                    result.geo_source,
                    raw_payload,
                ),
            )
            conn.commit()
        logger.debug("Cached geocode result for '%s'", normalized_address)


class GeocodingProvider(Protocol):
    """Protocol implemented by concrete geocoding providers."""

    name: str

    def geocode(self, normalized_address: str) -> GeocodeResult | None:
        ...


class NominatimGeocodingProvider:
    """Geocoding via OpenStreetMap's Nominatim API."""

    name = "nominatim"

    def __init__(
        self,
        *,
        rate_limiter: RateLimiter,
        user_agent: str,
        base_url: str | None = None,
        timeout: float = 10,
        retries: int = 3,
        backoff_factor: float = 1.5,
    ) -> None:
        self.rate_limiter = rate_limiter
        self.user_agent = user_agent
        self.base_url = base_url or "https://nominatim.openstreetmap.org/search"
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor

    def geocode(self, normalized_address: str) -> GeocodeResult | None:
        params = {
            "q": normalized_address,
            "format": "json",
            "addressdetails": 1,
            "limit": 1,
        }

        headers = {"User-Agent": self.user_agent}
        for attempt in range(1, self.retries + 1):
            self.rate_limiter.wait()
            try:
                response = requests.get(
                    self.base_url, params=params, headers=headers, timeout=self.timeout
                )
            except requests.RequestException as exc:  # pragma: no cover - network issues
                logger.warning("Nominatim request failed (attempt %s): %s", attempt, exc)
                self._sleep(attempt)
                continue

            if response.status_code in (429, 500, 502, 503, 504):
                logger.warning(
                    "Nominatim throttled or unavailable (status %s, attempt %s)",
                    response.status_code,
                    attempt,
                )
                self._sleep(attempt)
                continue

            if not response.ok:
                logger.error(
                    "Nominatim returned error status %s for '%s'", response.status_code, normalized_address
                )
                return None

            try:
                payload: list[dict[str, Any]] = response.json()
            except ValueError:
                logger.error("Unable to parse Nominatim response for '%s'", normalized_address)
                return None

            if not payload:
                return None

            result = payload[0]
            try:
                lat = float(result.get("lat"))
                lon = float(result.get("lon"))
            except (TypeError, ValueError):
                logger.error("Nominatim missing coordinates for '%s'", normalized_address)
                return None

            return GeocodeResult(
                lat=lat,
                lon=lon,
                formatted_address=result.get("display_name"),
                geo_precision=result.get("type") or result.get("class"),
                geo_source=self.name,
                raw=result,
            )

        return None

    def _sleep(self, attempt: int) -> None:
        delay = self.backoff_factor ** (attempt - 1)
        time.sleep(delay)


class GoogleGeocodingProvider:
    """Geocoding via the Google Maps Geocoding API."""

    name = "google"

    def __init__(
        self,
        *,
        api_key: str,
        rate_limiter: RateLimiter,
        base_url: str | None = None,
        timeout: float = 10,
        retries: int = 3,
        backoff_factor: float = 1.5,
    ) -> None:
        if not api_key:
            raise ValueError("Google geocoding requires an API key")

        self.api_key = api_key
        self.rate_limiter = rate_limiter
        self.base_url = base_url or "https://maps.googleapis.com/maps/api/geocode/json"
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor

    def geocode(self, normalized_address: str) -> GeocodeResult | None:
        params = {"address": normalized_address, "key": self.api_key}

        for attempt in range(1, self.retries + 1):
            self.rate_limiter.wait()
            try:
                response = requests.get(self.base_url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:  # pragma: no cover - network issues
                logger.warning("Google geocoding failed (attempt %s): %s", attempt, exc)
                self._sleep(attempt)
                continue

            if response.status_code in (429, 500, 502, 503, 504):
                logger.warning(
                    "Google geocoding throttled/unavailable (status %s, attempt %s)",
                    response.status_code,
                    attempt,
                )
                self._sleep(attempt)
                continue

            try:
                payload: dict[str, Any] = response.json()
            except ValueError:
                logger.error("Unable to parse Google response for '%s'", normalized_address)
                return None

            status = payload.get("status")
            if status == "OVER_QUERY_LIMIT":
                logger.warning("Google rate limit hit (attempt %s)", attempt)
                self._sleep(attempt)
                continue
            if status not in {"OK", "ZERO_RESULTS"}:
                logger.error("Google geocoding error '%s' for '%s'", status, normalized_address)
                return None
            results = payload.get("results") or []
            if not results:
                return None

            first = results[0]
            location = (first.get("geometry") or {}).get("location") or {}
            lat, lon = location.get("lat"), location.get("lng")
            if lat is None or lon is None:
                return None

            return GeocodeResult(
                lat=float(lat),
                lon=float(lon),
                formatted_address=first.get("formatted_address"),
                geo_precision=(first.get("geometry") or {}).get("location_type"),
                geo_source=self.name,
                raw=first,
            )

        return None

    def _sleep(self, attempt: int) -> None:
        delay = self.backoff_factor ** (attempt - 1)
        time.sleep(delay)


class GeocodingClient:
    """Facade that consults cache before invoking the provider."""

    def __init__(self, provider: GeocodingProvider, cache: GeocodeCache):
        self.provider = provider
        self.cache = cache

    def geocode(self, normalized_address: str) -> GeocodeResult | None:
        """
        Geocode an address, using cache if available.
        
        Note: This method is not thread-safe. In a multi-threaded environment,
        there's a potential race condition between checking the cache and storing
        the result, which could lead to duplicate API calls. This is acceptable
        for the current single-threaded use case.
        """
        cached = self.cache.fetch(normalized_address)
        if cached:
            return cached

        result = self.provider.geocode(normalized_address)
        if result:
            self.cache.store(normalized_address, result)
        return result


def build_geocoding_client(
    config: GeocoderConfig, *, provider_override: str | None = None
) -> GeocodingClient:
    """Create a :class:`GeocodingClient` using the provided configuration."""

    provider_name = (provider_override or config.provider.value).lower()
    rate_limiter = RateLimiter(config.rate_limit_per_sec)

    if provider_name == GeocoderProvider.GOOGLE.value:
        provider = GoogleGeocodingProvider(
            api_key=config.api_key or "",
            rate_limiter=rate_limiter,
            base_url=config.base_url,
            timeout=config.request_timeout_sec,
            retries=config.retries,
            backoff_factor=config.backoff_factor,
        )
    elif provider_name == GeocoderProvider.NOMINATIM.value:
        provider = NominatimGeocodingProvider(
            rate_limiter=rate_limiter,
            user_agent=config.user_agent,
            base_url=config.base_url,
            timeout=config.request_timeout_sec,
            retries=config.retries,
            backoff_factor=config.backoff_factor,
        )
    else:
        raise ValueError(f"Unsupported geocoder provider: {provider_name}")

    cache = GeocodeCache(config.cache_path)
    return GeocodingClient(provider=provider, cache=cache)


__all__ = [
    "GeocodeResult",
    "RateLimiter",
    "GeocodeCache",
    "GeocodingProvider",
    "NominatimGeocodingProvider",
    "GoogleGeocodingProvider",
    "GeocodingClient",
    "build_geocoding_client",
]

