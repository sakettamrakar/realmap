"""Protocols and default implementations for project geocoding."""

from __future__ import annotations

from typing import Protocol

from cg_rera_extractor.db import Project


class GeocodingStatus:
    """String constants describing geocoding states."""

    NOT_GEOCODED = "NOT_GEOCODED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Geocoder(Protocol):
    """Protocol for geocoding projects."""

    source: str | None

    def geocode_project(self, project: Project) -> tuple[float, float] | None:
        """Return ``(latitude, longitude)`` for the project or ``None`` if unknown."""


class NoopGeocoder:
    """Placeholder geocoder that never resolves coordinates."""

    source = "NOOP"

    def geocode_project(self, project: Project) -> None:  # pragma: no cover - trivial
        return None


__all__ = ["Geocoder", "GeocodingStatus", "NoopGeocoder"]
