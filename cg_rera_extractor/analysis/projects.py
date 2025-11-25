"""Helpers for power users to inspect and export project data."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Sequence

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from cg_rera_extractor.analysis import SessionLocal
from cg_rera_extractor.db import Project, ProjectAmenityStats, ProjectScores


@dataclass
class ProjectScoreSummary:
    """Normalized view of a project's score fields."""

    amenity_score: int | None
    location_score: int | None
    connectivity_score: int | None
    daily_needs_score: int | None
    social_infra_score: int | None
    overall_score: int | None
    score_version: str | None


@dataclass
class AmenityContext:
    """Simplified amenity slice summary for display/export."""

    amenity_type: str
    radius_km: float | None
    nearby_count: int | None
    nearest_km: float | None
    onsite_available: bool | None
    onsite_details: dict[str, Any] | None


@dataclass
class ProjectSummary:
    """Container for the most common project details."""

    project: dict[str, Any]
    scores: ProjectScoreSummary | None
    onsite_amenities: list[AmenityContext]
    location_context: list[AmenityContext]


# ---- Session helpers ------------------------------------------------------


def _get_session(session: Session | None) -> tuple[Session, bool]:
    if session:
        return session, False
    return SessionLocal(), True


# ---- Converters -----------------------------------------------------------


def _to_float(value: Decimal | float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _normalize_stat(stat: ProjectAmenityStats) -> AmenityContext:
    return AmenityContext(
        amenity_type=stat.amenity_type,
        radius_km=_to_float(stat.radius_km),
        nearby_count=stat.nearby_count,
        nearest_km=_to_float(stat.nearby_nearest_km),
        onsite_available=stat.onsite_available,
        onsite_details=stat.onsite_details or None,
    )


# ---- Queries --------------------------------------------------------------


def _project_with_related() -> Select[tuple[Project]]:
    return select(Project).options(
        selectinload(Project.score),
        selectinload(Project.amenity_stats),
        selectinload(Project.locations),
    )


def get_project_summary(
    project_reg_or_id: str | int, session: Session | None = None
) -> ProjectSummary:
    """Return a structured summary for a project by registration number or ID."""

    db, owns_session = _get_session(session)
    try:
        stmt = _project_with_related()
        if isinstance(project_reg_or_id, int):
            stmt = stmt.where(Project.id == project_reg_or_id)
        else:
            stmt = stmt.where(
                Project.rera_registration_number == str(project_reg_or_id)
            )

        project = db.execute(stmt).scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        scores = None
        if project.score:
            scores = ProjectScoreSummary(
                amenity_score=project.score.amenity_score,
                location_score=project.score.location_score,
                connectivity_score=project.score.connectivity_score,
                daily_needs_score=project.score.daily_needs_score,
                social_infra_score=project.score.social_infra_score,
                overall_score=project.score.overall_score,
                score_version=project.score.score_version,
            )

        onsite = [
            _normalize_stat(stat)
            for stat in project.amenity_stats
            if stat.radius_km is None and (stat.onsite_available or stat.onsite_details)
        ]

        location_context = _summarize_nearby(project.amenity_stats)

        return ProjectSummary(
            project={
                "id": project.id,
                "state_code": project.state_code,
                "rera_registration_number": project.rera_registration_number,
                "project_name": project.project_name,
                "status": project.status,
                "district": project.district,
                "tehsil": project.tehsil,
                "village_or_locality": project.village_or_locality,
                "full_address": project.full_address,
                "latitude": _to_float(project.latitude),
                "longitude": _to_float(project.longitude),
            },
            scores=scores,
            onsite_amenities=sorted(onsite, key=lambda x: x.amenity_type),
            location_context=location_context,
        )
    finally:
        if owns_session:
            db.close()


def _summarize_nearby(stats: Iterable[ProjectAmenityStats]) -> list[AmenityContext]:
    best_by_type: dict[str, AmenityContext] = {}

    for stat in stats:
        if stat.radius_km is None:
            continue
        normalized = _normalize_stat(stat)
        current = best_by_type.get(stat.amenity_type)
        # Prefer the smallest radius, falling back to any available slice.
        if current is None:
            best_by_type[stat.amenity_type] = normalized
            continue

        if normalized.radius_km is None:
            continue
        if current.radius_km is None or normalized.radius_km < current.radius_km:
            best_by_type[stat.amenity_type] = normalized

    return sorted(best_by_type.values(), key=lambda x: x.amenity_type)


def top_projects_by_score(
    district: str | None = None,
    limit: int = 50,
    min_score: int | None = None,
    session: Session | None = None,
) -> list[dict[str, Any]]:
    """Return high-scoring projects with basic metadata."""

    db, owns_session = _get_session(session)
    try:
        stmt = (
            select(Project, ProjectScores)
            .join(ProjectScores, ProjectScores.project_id == Project.id)
            .order_by(ProjectScores.overall_score.desc(), Project.project_name)
            .limit(limit)
        )

        if district:
            stmt = stmt.where(Project.district.ilike(district))

        if min_score is not None:
            stmt = stmt.where(ProjectScores.overall_score >= min_score)

        results: list[dict[str, Any]] = []
        for project, scores in db.execute(stmt).all():
            results.append(
                {
                    "id": project.id,
                    "state_code": project.state_code,
                    "rera_registration_number": project.rera_registration_number,
                    "project_name": project.project_name,
                    "district": project.district,
                    "status": project.status,
                    "overall_score": scores.overall_score,
                    "amenity_score": scores.amenity_score,
                    "location_score": scores.location_score,
                    "connectivity_score": scores.connectivity_score,
                    "daily_needs_score": scores.daily_needs_score,
                    "social_infra_score": scores.social_infra_score,
                    "score_version": scores.score_version,
                }
            )

        return results
    finally:
        if owns_session:
            db.close()


def export_projects_csv(
    filters: dict[str, Any], path: str | Path, session: Session | None = None
) -> Path:
    """Export project slices to CSV according to the provided filters."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    district = filters.get("district")
    limit = int(filters.get("limit", 50))
    min_score = filters.get("min_score")

    projects = top_projects_by_score(
        district=district,
        limit=limit,
        min_score=min_score,
        session=session,
    )

    if not projects:
        path.write_text("")
        return path

    fieldnames: Sequence[str] = (
        "id",
        "state_code",
        "rera_registration_number",
        "project_name",
        "district",
        "status",
        "overall_score",
        "amenity_score",
        "location_score",
        "connectivity_score",
        "daily_needs_score",
        "social_infra_score",
        "score_version",
    )

    import csv

    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(projects)

    return path


__all__ = [
    "AmenityContext",
    "ProjectScoreSummary",
    "ProjectSummary",
    "export_projects_csv",
    "get_project_summary",
    "top_projects_by_score",
]
