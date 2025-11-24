"""Computation helpers for per-project amenity statistics."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from cg_rera_extractor.amenities.cache import AmenityCache, haversine_distance_km
from cg_rera_extractor.db import ProjectAmenityStats

logger = logging.getLogger(__name__)


@dataclass
class AmenitySliceStats:
    """Aggregate metrics for a single amenity type and radius."""

    amenity_type: str
    radius_km: float
    count_within_radius: int
    nearest_distance_km: float | None


def _normalize_radii(radii: Iterable[float]) -> list[float]:
    unique = {float(radius) for radius in radii}
    return sorted(unique)


def compute_project_amenity_stats(
    *,
    lat: float,
    lon: float,
    amenity_cache: AmenityCache,
    search_radii_km: dict[str, Iterable[float]],
) -> list[AmenitySliceStats]:
    """Compute amenity counts and nearest distances for a project."""

    results: list[AmenitySliceStats] = []
    for amenity_type, radii in search_radii_km.items():
        normalized_radii = _normalize_radii(radii)
        if not normalized_radii:
            continue

        max_radius = normalized_radii[-1]
        amenities = amenity_cache.fetch_amenities(lat, lon, amenity_type, max_radius)
        if not amenities:
            for radius in normalized_radii:
                results.append(
                    AmenitySliceStats(
                        amenity_type=amenity_type,
                        radius_km=radius,
                        count_within_radius=0,
                        nearest_distance_km=None,
                    )
                )
            continue

        distances = [
            haversine_distance_km(lat, lon, amenity.lat, amenity.lon)
            for amenity in amenities
        ]

        for radius in normalized_radii:
            distances_within_radius = [d for d in distances if d <= radius]
            nearest_distance = min(distances_within_radius) if distances_within_radius else None
            results.append(
                AmenitySliceStats(
                    amenity_type=amenity_type,
                    radius_km=radius,
                    count_within_radius=len(distances_within_radius),
                    nearest_distance_km=nearest_distance,
                )
            )

    return results


def to_orm_rows(
    project_id: int,
    stats: Iterable[AmenitySliceStats],
    *,
    provider_snapshot: str | None,
) -> list[ProjectAmenityStats]:
    """Convert computed stats into ORM rows for persistence."""

    computed_at = datetime.now(timezone.utc)
    return [
        ProjectAmenityStats(
            project_id=project_id,
            amenity_type=stat.amenity_type,
            radius_km=stat.radius_km,
            count_within_radius=stat.count_within_radius,
            nearest_distance_km=stat.nearest_distance_km,
            provider_snapshot=provider_snapshot,
            last_computed_at=computed_at,
        )
        for stat in stats
    ]


__all__ = [
    "AmenitySliceStats",
    "compute_project_amenity_stats",
    "to_orm_rows",
]
