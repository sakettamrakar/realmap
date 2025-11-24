"""Amenity provider abstraction and concrete implementations."""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Protocol

import requests

from cg_rera_extractor.config.models import AmenitiesConfig, AmenityProvider as AmenityProviderChoice

logger = logging.getLogger(__name__)


@dataclass
class Amenity:
    """Normalized amenity payload returned by providers or cache."""

    amenity_type: str
    name: str | None
    lat: float
    lon: float
    formatted_address: str | None
    provider: str
    provider_place_id: str | None
    raw: dict | None = None


class AmenityProvider(Protocol):
    """Protocol that amenity providers must implement."""

    name: str

    def search(self, lat: float, lon: float, amenity_type: str, radius_km: float) -> list[Amenity]:
        """Return a list of amenities within the given radius."""


class RateLimiter:
    """Simple rate limiter using sleep-based throttling."""

    def __init__(self, requests_per_minute: float):
        interval = 60.0 / requests_per_minute if requests_per_minute > 0 else 0
        self.min_interval = interval
        self._last_request_at = 0.0

    def wait(self) -> None:
        """Block until sufficient time has passed since the last request.

        The timestamp is updated before returning to accurately reflect when
        the next request is about to be made.
        """
        if not self.min_interval:
            return
        now = time.monotonic()
        elapsed = now - self._last_request_at
        remaining = self.min_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)
        # Update timestamp immediately before returning so the caller
        # makes the request right after this returns.
        self._last_request_at = time.monotonic()


class OSMOverpassProvider:
    """Amenity provider backed by the Overpass API."""

    name = "osm"
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    AMENITY_TAGS: dict[str, list[tuple[str, str]]] = {
        "school": [("amenity", "school")],
        "college_university": [("amenity", "college"), ("amenity", "university")],
        "hospital": [("amenity", "hospital")],
        "clinic": [("amenity", "clinic"), ("amenity", "doctors")],
        "pharmacy": [("amenity", "pharmacy")],
        "supermarket": [("shop", "supermarket")],
        "grocery_convenience": [("shop", "convenience"), ("shop", "grocery")],
        "mall": [("shop", "mall")],
        "bank_atm": [("amenity", "bank"), ("amenity", "atm")],
        "restaurant_cafe": [
            ("amenity", "restaurant"),
            ("amenity", "cafe"),
            ("amenity", "fast_food"),
        ],
        "park_playground": [("leisure", "park"), ("leisure", "playground")],
        "transit_stop": [
            ("public_transport", "station"),
            ("public_transport", "stop_position"),
            ("railway", "station"),
            ("railway", "halt"),
            ("highway", "bus_stop"),
            ("railway", "stop"),
            ("railway", "tram_stop"),
        ],
    }

    def __init__(
        self,
        *,
        rate_limiter: RateLimiter,
        base_url: str | None = None,
        timeout: float = 15.0,
        retries: int = 3,
        backoff_factor: float = 1.5,
        session: requests.Session | None = None,
    ) -> None:
        self.rate_limiter = rate_limiter
        self.base_url = base_url or self.OVERPASS_URL
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.session = session or requests.Session()

    def search(self, lat: float, lon: float, amenity_type: str, radius_km: float) -> list[Amenity]:
        tags = self.AMENITY_TAGS.get(amenity_type)
        if not tags:
            logger.warning("Amenity type '%s' is not mapped to OSM tags", amenity_type)
            return []

        radius_m = max(1, int(radius_km * 1000))
        filters = [f'nwr["{key}"="{value}"](around:{radius_m},{lat},{lon});' for key, value in tags]
        query = f"[out:json];({' '.join(filters)});out center;"

        for attempt in range(1, self.retries + 1):
            self.rate_limiter.wait()
            try:
                response = self.session.post(
                    self.base_url, data={"data": query}, timeout=self.timeout
                )
            except requests.RequestException as exc:  # pragma: no cover - network failure
                logger.warning("Overpass request failed (attempt %s): %s", attempt, exc)
                self._sleep(attempt)
                continue

            if response.status_code in (429, 500, 502, 503, 504):
                logger.warning(
                    "Overpass throttled/unavailable (status %s, attempt %s)",
                    response.status_code,
                    attempt,
                )
                self._sleep(attempt)
                continue

            if not response.ok:
                logger.error(
                    "Overpass returned non-OK status %s: %s", response.status_code, response.text
                )
                return []

            try:
                payload = response.json()
            except json.JSONDecodeError:  # pragma: no cover - unexpected payload
                logger.error("Failed to decode Overpass response: %s", response.text[:200])
                return []

            elements = payload.get("elements", []) if isinstance(payload, dict) else []
            amenities: list[Amenity] = []
            seen_ids: set[str] = set()
            for element in elements:
                amenity = self._to_amenity(element, amenity_type)
                if not amenity:
                    continue
                if amenity.provider_place_id and amenity.provider_place_id in seen_ids:
                    continue
                if amenity.provider_place_id:
                    seen_ids.add(amenity.provider_place_id)
                amenities.append(amenity)
            return amenities

        return []

    def _sleep(self, attempt: int) -> None:
        delay = self.backoff_factor ** (attempt - 1)
        time.sleep(delay)

    def _to_amenity(self, element: dict, amenity_type: str) -> Amenity | None:
        raw_id = element.get("id")
        element_type = element.get("type")
        provider_place_id = None
        if raw_id is not None and element_type:
            provider_place_id = f"{element_type}/{raw_id}"

        tags = element.get("tags", {}) or {}
        lat = element.get("lat")
        lon = element.get("lon")
        center = element.get("center") or {}
        if lat is None or lon is None:
            lat = center.get("lat")
            lon = center.get("lon")
        if lat is None or lon is None:
            return None

        formatted_address = self._format_address(tags)
        name = tags.get("name") or tags.get("operator")
        return Amenity(
            amenity_type=amenity_type,
            name=name,
            lat=float(lat),
            lon=float(lon),
            formatted_address=formatted_address,
            provider=self.name,
            provider_place_id=str(provider_place_id) if provider_place_id else None,
            raw=element,
        )

    @staticmethod
    def _format_address(tags: dict[str, str]) -> str | None:
        components: list[str] = []
        for key in ("addr:housenumber", "addr:street", "addr:city", "addr:state", "addr:postcode"):
            value = tags.get(key)
            if value:
                components.append(value)
        return ", ".join(components) if components else None


def get_provider_from_config(config: AmenitiesConfig) -> AmenityProvider:
    """Return the amenity provider configured for the run."""

    if config.provider == AmenityProviderChoice.OSM:
        limiter = RateLimiter(requests_per_minute=config.rate_limit_per_minute)
        return OSMOverpassProvider(
            rate_limiter=limiter,
            timeout=config.request_timeout_sec,
            retries=config.retries,
            backoff_factor=config.backoff_factor,
        )

    if config.provider == AmenityProviderChoice.GOOGLE:
        raise NotImplementedError("Google Places provider not yet implemented")

    raise ValueError(f"Unsupported amenity provider: {config.provider}")


__all__ = [
    "Amenity",
    "AmenityProvider",
    "OSMOverpassProvider",
    "get_provider_from_config",
]
