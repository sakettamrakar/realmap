"""Project search service implementing filters and pagination."""
from __future__ import annotations

import math
from datetime import date
from typing import Iterable

from sqlalchemy.orm import Session, selectinload

from cg_rera_extractor.amenities.value_scoring import compute_value_score, get_value_bucket
from cg_rera_extractor.db import Project, ProjectAmenityStats


class SearchParams:
    """Container for search filters and pagination."""

    def __init__(
        self,
        *,
        district: str | None = None,
        tehsil: str | None = None,
        name_contains: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        project_types: list[str] | None = None,
        statuses: list[str] | None = None,
        amenities: list[str] | None = None,
        min_overall_score: float | None = None,
        min_location_score: float | None = None,
        min_amenity_score: float | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        # Point 24: Tag filtering
        tags: list[str] | None = None,
        tags_match_all: bool = False,
        # Point 25: RERA verification filter
        rera_verified_only: bool = False,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "overall_score",
        sort_dir: str = "desc",
    ) -> None:
        self.district = district
        self.tehsil = tehsil
        self.name_contains = name_contains
        self.lat = lat
        self.lon = lon
        self.radius_km = radius_km
        self.bbox = bbox
        self.project_types = project_types or []
        self.statuses = statuses or []
        self.amenities = amenities or []
        self.min_overall_score = min_overall_score
        self.min_location_score = min_location_score
        self.min_amenity_score = min_amenity_score
        self.min_price = min_price
        self.max_price = max_price
        # Point 24: Tag filtering
        self.tags = tags or []
        self.tags_match_all = tags_match_all
        # Point 25: RERA verification filter
        self.rera_verified_only = rera_verified_only
        self.page = page
        self.page_size = page_size
        self.sort_by = sort_by
        self.sort_dir = sort_dir


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute distance between two points using the Haversine formula."""

    radius = 6371  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def _resolve_location(project: Project) -> tuple[float | None, float | None, str | None]:
    """Return a canonical lat/lon for a project with a geo quality hint."""

    active_location = next((loc for loc in project.locations if loc.is_active), None)
    if active_location:
        return float(active_location.lat), float(active_location.lon), active_location.precision_level

    if project.latitude is not None and project.longitude is not None:
        return float(project.latitude), float(project.longitude), project.geo_precision

    return None, None, None


def _score_to_float(score: int | None) -> float | None:
    if score is None:
        return None
    return float(score) if score is not None else None


def _onsite_amenities(stats: Iterable[ProjectAmenityStats]) -> tuple[list[str], dict[str, int]]:
    onsite = [s for s in stats if s.radius_km is None and s.onsite_available]
    highlight = [s.amenity_type for s in onsite]
    counts = {"total": len(onsite), "primary": len(onsite)} if onsite else {"total": 0, "primary": 0}
    return highlight, counts


def _nearby_counts(stats: Iterable[ProjectAmenityStats]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for stat in stats:
        if stat.radius_km is None:
            continue
        # Prefer the smallest radius for each amenity type when multiple slices exist.
        existing = summary.get(stat.amenity_type)
        if existing is None:
            summary[stat.amenity_type] = stat.nearby_count or 0
    return summary


def _get_latest_price(project: Project) -> dict[str, float | None]:
    if not project.pricing_snapshots:
        return {}
    
    # Filter active snapshots
    active = [s for s in project.pricing_snapshots if s.is_active]
    if not active:
        return {}
        
    # Find latest date
    latest_date = max(s.snapshot_date for s in active)
    
    # Filter for latest date
    latest_snapshots = [s for s in active if s.snapshot_date == latest_date]
    
    # Aggregate
    min_totals = [s.min_price_total for s in latest_snapshots if s.min_price_total is not None]
    max_totals = [s.max_price_total for s in latest_snapshots if s.max_price_total is not None]
    min_sqfts = [s.min_price_per_sqft for s in latest_snapshots if s.min_price_per_sqft is not None]
    max_sqfts = [s.max_price_per_sqft for s in latest_snapshots if s.max_price_per_sqft is not None]
    
    return {
        "min_price_total": float(min(min_totals)) if min_totals else None,
        "max_price_total": float(max(max_totals)) if max_totals else None,
        "min_price_per_sqft": float(min(min_sqfts)) if min_sqfts else None,
        "max_price_per_sqft": float(max(max_sqfts)) if max_sqfts else None,
    }


def search_projects(db: Session, params: SearchParams) -> tuple[int, list[dict]]:
    """Search projects applying filters and returning pagination metadata."""

    stmt = (
        db.query(Project)
        .options(
            selectinload(Project.score),
            selectinload(Project.amenity_stats),
            selectinload(Project.locations),
            selectinload(Project.pricing_snapshots),
        )
    )

    if params.district:
        stmt = stmt.filter(Project.district.ilike(params.district))
    if params.tehsil:
        stmt = stmt.filter(Project.tehsil.ilike(params.tehsil))
    if params.name_contains:
        stmt = stmt.filter(Project.project_name.ilike(f"%{params.name_contains}%"))
    
    if params.statuses:
        # Case insensitive check for statuses
        # Since we can't easily do ilike on a list, we might need to rely on exact match 
        # or normalize in Python. Let's try exact match first as statuses are usually standardized.
        # If they are not, we might need to normalize them.
        stmt = stmt.filter(Project.status.in_(params.statuses))
        
    if params.project_types:
        # Assuming project_type is in raw_data_json for now as it's not a column
        # Using astext for Postgres JSONB
        stmt = stmt.filter(Project.raw_data_json["project_type"].astext.in_(params.project_types))

    if params.bbox:
        min_lat, min_lon, max_lat, max_lon = params.bbox
        stmt = stmt.filter(
            Project.latitude.is_not(None),
            Project.longitude.is_not(None),
            Project.latitude.between(min_lat, max_lat),
            Project.longitude.between(min_lon, max_lon),
        )

    projects = stmt.all()

    filtered: list[tuple[Project, float | None]] = []
    for project in projects:
        lat, lon, _quality = _resolve_location(project)
        if lat is None or lon is None:
            continue

        if params.lat is not None and params.lon is not None and params.radius_km is not None:
            distance = _haversine_km(params.lat, params.lon, lat, lon)
            if distance > params.radius_km:
                continue
        else:
            distance = None

        filtered.append((project, distance))

    # Apply amenity filter in-memory using onsite flags.
    amenity_filtered: list[tuple[Project, float | None]] = []
    for project, distance in filtered:
        if params.amenities:
            onsite = {stat.amenity_type for stat in project.amenity_stats if stat.radius_km is None and stat.onsite_available}
            if not set(params.amenities).issubset(onsite):
                continue
        amenity_filtered.append((project, distance))

    # Score and Price filters
    final_projects: list[tuple[Project, float | None]] = []
    for project, distance in amenity_filtered:
        scores = project.score
        
        # Score filters
        if params.min_overall_score is not None:
            if scores is None or _score_to_float(scores.overall_score) is None:
                continue
            if _score_to_float(scores.overall_score) < params.min_overall_score:
                continue
        if params.min_location_score is not None:
            if scores is None or _score_to_float(scores.location_score) is None:
                continue
            if _score_to_float(scores.location_score) < params.min_location_score:
                continue
        if params.min_amenity_score is not None:
            if scores is None or _score_to_float(scores.amenity_score) is None:
                continue
            if _score_to_float(scores.amenity_score) < params.min_amenity_score:
                continue
        
        # Price filters
        price_info = _get_latest_price(project)
        if params.min_price is not None:
            # If no price info, exclude? Or include? Usually exclude if filter is active.
            if price_info.get("max_price_total") is None: 
                continue
            # Filter: project max price >= user min budget
            if price_info["max_price_total"] < params.min_price:
                continue
        
        if params.max_price is not None:
            if price_info.get("min_price_total") is None:
                continue
            # Filter: project min price <= user max budget
            if price_info["min_price_total"] > params.max_price:
                continue

        final_projects.append((project, distance))

    # Point 24: Tag filtering
    if params.tags:
        from cg_rera_extractor.api.services.discovery import get_projects_by_tags
        
        # Get project IDs matching tag filter
        tag_project_ids = set(get_projects_by_tags(
            db, 
            params.tags, 
            match_all=params.tags_match_all
        ))
        
        # Filter to only projects with matching tags
        final_projects = [
            (p, d) for p, d in final_projects 
            if p.id in tag_project_ids
        ]

    # Point 25: RERA verified filter
    if params.rera_verified_only:
        from cg_rera_extractor.db.models_discovery import ReraVerification
        from cg_rera_extractor.db.enums import ReraVerificationStatus
        from sqlalchemy import select
        
        # Get verified project IDs
        verified_query = (
            select(ReraVerification.project_id)
            .where(ReraVerification.is_current == True)
            .where(ReraVerification.status == ReraVerificationStatus.VERIFIED)
        )
        verified_ids = set(row[0] for row in db.execute(verified_query))
        
        final_projects = [
            (p, d) for p, d in final_projects
            if p.id in verified_ids
        ]

    # Sorting
    reverse = params.sort_dir.lower() != "asc"

    def sort_key(item: tuple[Project, float | None]):
        project, distance = item
        score = project.score
        if params.sort_by == "distance":
            return distance if distance is not None else float("inf")
        if params.sort_by == "location_score" and score:
            return _score_to_float(score.location_score) or 0
        if params.sort_by == "amenity_score" and score:
            return _score_to_float(score.amenity_score) or 0
        if params.sort_by == "registration_date":
            return project.approved_date or project.proposed_end_date or project.extended_end_date or date.min
        if params.sort_by == "price":
            p = _get_latest_price(project)
            return p.get("min_price_total") or float("inf") # Sort by min price
        if params.sort_by == "value_score":
            # Compute value_score for sorting
            p = _get_latest_price(project)
            overall = _score_to_float(score.overall_score) if score else None
            if score and score.value_score is not None:
                return _score_to_float(score.value_score) or 0
            elif overall is not None and p.get("min_price_total"):
                return compute_value_score(overall, p.get("min_price_total"), p.get("max_price_total")) or 0
            return 0
        if params.sort_by == "name":
            return project.project_name.lower()
            
        return _score_to_float(score.overall_score) if score else 0

    final_projects.sort(key=sort_key, reverse=reverse)

    total = len(final_projects)
    start = (params.page - 1) * params.page_size
    end = start + params.page_size
    page_items = final_projects[start:end]

    payload: list[dict] = []
    
    # Pre-fetch tag data for all projects in page (efficient batch query)
    page_project_ids = [p.id for p, _ in page_items]
    project_tags_map: dict[int, list[str]] = {}
    project_verification_map: dict[int, str] = {}
    
    if page_project_ids:
        from cg_rera_extractor.db.models_discovery import ProjectTag, ReraVerification, Tag
        from sqlalchemy import select
        
        # Batch fetch tags
        tags_query = (
            select(ProjectTag.project_id, Tag.slug)
            .join(Tag, Tag.id == ProjectTag.tag_id)
            .where(ProjectTag.project_id.in_(page_project_ids))
            .where(Tag.is_active == True)
        )
        for project_id, tag_slug in db.execute(tags_query):
            if project_id not in project_tags_map:
                project_tags_map[project_id] = []
            project_tags_map[project_id].append(tag_slug)
        
        # Batch fetch RERA verification status
        verification_query = (
            select(ReraVerification.project_id, ReraVerification.status)
            .where(ReraVerification.project_id.in_(page_project_ids))
            .where(ReraVerification.is_current == True)
        )
        for project_id, status in db.execute(verification_query):
            project_verification_map[project_id] = status.value if hasattr(status, 'value') else str(status)
    
    for project, distance in page_items:
        lat, lon, quality = _resolve_location(project)
        scores = project.score
        highlight, onsite_counts = _onsite_amenities(project.amenity_stats)
        nearby_counts = _nearby_counts(project.amenity_stats)
        price_info = _get_latest_price(project)
        
        # Compute value_score - use stored value or compute on the fly
        value_score = None
        if scores and scores.value_score is not None:
            value_score = _score_to_float(scores.value_score)
        elif scores and scores.overall_score is not None and price_info.get("min_price_total"):
            value_score = compute_value_score(
                _score_to_float(scores.overall_score),
                price_info.get("min_price_total"),
                price_info.get("max_price_total"),
            )
        value_bucket = get_value_bucket(value_score)

        payload.append(
            {
                "project_id": project.id,
                "name": project.project_name,
                "district": project.district,
                "tehsil": project.tehsil,
                "project_type": project.raw_data_json.get("project_type") if project.raw_data_json else None,
                "status": project.status,
                "lat": lat,
                "lon": lon,
                "geo_quality": quality or project.geo_precision or project.geo_source,
                "overall_score": _score_to_float(scores.overall_score) if scores else None,
                "location_score": _score_to_float(scores.location_score) if scores else None,
                "amenity_score": _score_to_float(scores.amenity_score) if scores else None,
                "value_score": value_score,
                "value_bucket": value_bucket,
                "score_status": scores.score_status if scores else None,
                "score_status_reason": scores.score_status_reason if scores else None,
                "units": None,
                "area_sqft": None,
                "registration_date": project.approved_date,
                "distance_km": distance,
                "highlight_amenities": highlight,
                "onsite_amenity_counts": onsite_counts,
                "nearby_counts": nearby_counts,
                "min_price_total": price_info.get("min_price_total"),
                "max_price_total": price_info.get("max_price_total"),
                "min_price_per_sqft": price_info.get("min_price_per_sqft"),
                "max_price_per_sqft": price_info.get("max_price_per_sqft"),
                # Point 24-25: Discovery data
                "tags": project_tags_map.get(project.id, []),
                "rera_verification_status": project_verification_map.get(project.id),
            }
        )

    return total, payload


__all__ = ["search_projects", "SearchParams"]


__all__ = ["search_projects", "SearchParams"]
