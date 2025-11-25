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
    amenity_type: str
    radius_km: float | None
    
    # Nearby
    nearby_count: int | None
    nearby_nearest_km: float | None
    
    # Onsite
    onsite_available: bool | None
    onsite_details: dict | None


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
                        nearby_count=0,
                        nearby_nearest_km=None,
                        onsite_available=False, # Default assumption for now
                        onsite_details=None,
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
                    nearby_count=len(distances_within_radius),
                    nearby_nearest_km=nearest_distance,
                    onsite_available=False, # Placeholder, will be populated from RERA data later
                    onsite_details=None,
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
            nearby_count=stat.nearby_count,
            nearby_nearest_km=stat.nearby_nearest_km,
            onsite_available=stat.onsite_available,
            onsite_details=stat.onsite_details,
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
