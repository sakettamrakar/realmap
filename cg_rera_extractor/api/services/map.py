"""Map pin service for lightweight project feeds."""
from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from cg_rera_extractor.db import Project

from .search import _haversine_km, _resolve_location, _score_to_float


def fetch_map_projects(
    db: Session,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    center: tuple[float, float] | None = None,
    radius_km: float | None = None,
    min_overall_score: float | None = None,
    project_type: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """Return pins constrained by a bounding box or center/radius."""

    stmt = db.query(Project).options(selectinload(Project.score), selectinload(Project.locations))

    if status:
        stmt = stmt.filter(Project.status.ilike(status))

    if bbox:
        min_lat, min_lon, max_lat, max_lon = bbox
        stmt = stmt.filter(
            Project.latitude.is_not(None),
            Project.longitude.is_not(None),
            Project.latitude.between(min_lat, max_lat),
            Project.longitude.between(min_lon, max_lon),
        )

    projects = stmt.all()
    pins: list[dict] = []
    for project in projects:
        lat, lon, quality = _resolve_location(project)
        if lat is None or lon is None:
            continue

        scores = project.score
        overall_score = _score_to_float(scores.overall_score) if scores else None
        if min_overall_score is not None and (overall_score is None or overall_score < min_overall_score):
            continue

        if center and radius_km is not None:
            center_lat, center_lon = center
            distance = _haversine_km(center_lat, center_lon, lat, lon)
            if distance > radius_km:
                continue

        pins.append(
            {
                "project_id": project.id,
                "name": project.project_name,
                "lat": lat,
                "lon": lon,
                "overall_score": overall_score,
                "project_type": project.project_name,
                "status": project.status,
                "size_hint": {"units": None, "area_sqft": None},
            }
        )

    return pins


__all__ = ["fetch_map_projects"]
