"""Batch geocoding utilities for CG RERA projects."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from cg_rera_extractor.db import Project

from .interface import Geocoder, GeocodingStatus


def geocode_missing_projects(
    session: Session, geocoder: Geocoder, limit: int = 100
) -> dict[str, int]:
    """Geocode projects lacking coordinates.

    Projects with ``geocoding_status`` set to ``None`` or
    :data:`~cg_rera_extractor.geo.interface.GeocodingStatus.NOT_GEOCODED` are
    selected up to ``limit``. Each is passed to the provided ``geocoder``;
    successes update ``latitude``, ``longitude``, ``geocoding_status``, and
    ``geocoding_source``. Failures leave coordinates unset and mark status as
    ``NOT_GEOCODED`` so they can be retried later.
    """

    counts: dict[str, int] = defaultdict(int)
    stmt = (
        select(Project)
        .where(
            (Project.geocoding_status.is_(None))
            | (Project.geocoding_status == GeocodingStatus.NOT_GEOCODED)
        )
        .limit(limit)
    )

    projects = session.scalars(stmt).all()
    for project in projects:
        counts["processed"] += 1
        project.geocoding_status = GeocodingStatus.PENDING

        try:
            coordinates = geocoder.geocode_project(project)
        except Exception:
            project.geocoding_status = GeocodingStatus.FAILED
            counts["failed"] += 1
            continue

        if coordinates is None:
            project.geocoding_status = GeocodingStatus.NOT_GEOCODED
            counts["not_geocoded"] += 1
            continue

        latitude, longitude = coordinates
        project.latitude = latitude
        project.longitude = longitude
        project.geocoding_status = GeocodingStatus.SUCCESS
        project.geocoding_source = getattr(geocoder, "source", None)
        counts["success"] += 1

    session.commit()
    return dict(counts)


__all__ = ["geocode_missing_projects"]
