"""Local caching layer for amenities backed by the ``amenity_poi`` table."""
from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from cg_rera_extractor.amenities.provider import Amenity, AmenityProvider
from cg_rera_extractor.db import AmenityPOI

logger = logging.getLogger(__name__)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in kilometers between two coordinates."""

    radius_earth_km = 6371.0
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(
        math.radians, [lat1, lon1, lat2, lon2]
    )
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_earth_km * c


class AmenityCache:
    """Amenity cache wrapper that checks ``amenity_poi`` before provider calls."""

    def __init__(
        self,
        *,
        provider: AmenityProvider,
        session_factory: Callable[[], Session],
        freshness_days: int = 60,
    ) -> None:
        self.provider = provider
        self.session_factory = session_factory
        self.freshness_days = freshness_days

    def fetch_amenities(
        self, lat: float, lon: float, amenity_type: str, radius_km: float
    ) -> list[Amenity]:
        """Fetch amenities, preferring cached rows when sufficiently fresh."""

        session = self.session_factory()
        try:
            cached = self._get_cached(session, lat, lon, amenity_type, radius_km)
            if cached:
                logger.debug(
                    "Cache hit for amenity_type=%s radius=%.2fkm (lat=%.5f, lon=%.5f)",
                    amenity_type,
                    radius_km,
                    lat,
                    lon,
                )
                return cached

            logger.info(
                "Cache miss; querying provider '%s' for amenity_type=%s radius=%.2fkm",
                self.provider.name,
                amenity_type,
                radius_km,
            )
            amenities = self.provider.search(lat, lon, amenity_type, radius_km)
            if not amenities:
                return []

            self._upsert(session, amenities)
            session.commit()
            return amenities
        finally:
            session.close()

    def _get_cached(
        self,
        session: Session,
        lat: float,
        lon: float,
        amenity_type: str,
        radius_km: float,
    ) -> list[Amenity]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.freshness_days)
        degree_buffer = radius_km / 111.0

        stmt = (
            select(AmenityPOI)
            .where(AmenityPOI.amenity_type == amenity_type)
            .where(AmenityPOI.last_seen_at >= cutoff)
            .where(AmenityPOI.lat.between(lat - degree_buffer, lat + degree_buffer))
            .where(AmenityPOI.lon.between(lon - degree_buffer, lon + degree_buffer))
        )
        rows: Iterable[AmenityPOI] = session.scalars(stmt)
        amenities: list[Amenity] = []
        for poi in rows:
            poi_lat = float(poi.lat)
            poi_lon = float(poi.lon)
            distance_km = haversine_distance_km(lat, lon, poi_lat, poi_lon)
            if distance_km <= radius_km:
                amenities.append(
                    Amenity(
                        amenity_type=poi.amenity_type,
                        name=poi.name,
                        lat=poi_lat,
                        lon=poi_lon,
                        formatted_address=poi.formatted_address,
                        provider=poi.provider,
                        provider_place_id=poi.provider_place_id,
                        raw=poi.source_raw,
                    )
                )
        return amenities

    def _upsert(self, session: Session, amenities: list[Amenity]) -> None:
        for amenity in amenities:
            place_id = amenity.provider_place_id or (
                f"{amenity.amenity_type}:{amenity.lat:.6f},{amenity.lon:.6f}"
            )
            stmt = select(AmenityPOI).where(
                AmenityPOI.provider == amenity.provider,
                AmenityPOI.provider_place_id == place_id,
            )
            existing = session.scalars(stmt).first()
            if existing:
                existing.name = amenity.name
                existing.amenity_type = amenity.amenity_type
                existing.lat = amenity.lat
                existing.lon = amenity.lon
                existing.formatted_address = amenity.formatted_address
                existing.source_raw = amenity.raw
                existing.touch_last_seen()
            else:
                session.add(
                    AmenityPOI(
                        provider=amenity.provider,
                        provider_place_id=place_id,
                        amenity_type=amenity.amenity_type,
                        name=amenity.name,
                        lat=amenity.lat,
                        lon=amenity.lon,
                        formatted_address=amenity.formatted_address,
                        source_raw=amenity.raw,
                        last_seen_at=datetime.now(timezone.utc),
                    )
                )


__all__ = ["AmenityCache", "haversine_distance_km"]
