"""Project-related API routes implementing Phase 6 endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from cg_rera_extractor.api.deps import get_db
from cg_rera_extractor.api.schemas import (
    ProjectDetailV2,
    ProjectMapResponse,
    ProjectSearchResponse,
)
from cg_rera_extractor.api.services import fetch_map_projects, fetch_project_detail, search_projects
from cg_rera_extractor.api.services.search import SearchParams

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/search", response_model=ProjectSearchResponse)
def search_projects_endpoint(
    *,
    district: str | None = None,
    tehsil: str | None = None,
    name_contains: str | None = None,
    lat: float | None = Query(None, ge=-90, le=90),
    lon: float | None = Query(None, ge=-180, le=180),
    radius_km: float | None = Query(None, gt=0),
    bbox: str | None = None,
    project_types: list[str] | None = Query(None, alias="project_types"),
    statuses: list[str] | None = Query(None, alias="statuses"),
    amenities: str | None = None,
    min_overall_score: float | None = Query(None, ge=0, le=1),
    min_location_score: float | None = Query(None, ge=0, le=1),
    min_amenity_score: float | None = Query(None, ge=0, le=1),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    sort_by: str = Query("overall_score", pattern="^(overall_score|location_score|amenity_score|value_score|registration_date|distance|price|name)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db=Depends(get_db),
):
    bbox_tuple = None
    if bbox:
        try:
            parts = [float(p) for p in bbox.split(",")]
            if len(parts) != 4:
                raise ValueError
            bbox_tuple = (parts[0], parts[1], parts[2], parts[3])
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid bbox format") from exc

    amenity_list = [a.strip() for a in amenities.split(",")] if amenities else []

    params = SearchParams(
        district=district,
        tehsil=tehsil,
        name_contains=name_contains,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        bbox=bbox_tuple,
        project_types=project_types,
        statuses=statuses,
        amenities=amenity_list,
        min_overall_score=min_overall_score,
        min_location_score=min_location_score,
        min_amenity_score=min_amenity_score,
        min_price=min_price,
        max_price=max_price,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )

    total, items = search_projects(db, params)
    return ProjectSearchResponse(page=page, page_size=page_size, total=total, items=items)


@router.get("/map", response_model=ProjectMapResponse)
def map_endpoint(
    *,
    bbox: str | None = Query(None),
    lat: float | None = Query(None, ge=-90, le=90),
    lon: float | None = Query(None, ge=-180, le=180),
    radius_km: float | None = Query(None, gt=0),
    min_overall_score: float | None = Query(None, ge=0, le=1),
    project_type: str | None = None,
    status: str | None = None,
    db=Depends(get_db),
):
    if not bbox and (lat is None or lon is None):
        raise HTTPException(status_code=400, detail="Either bbox or lat/lon must be provided")

    bbox_tuple = None
    if bbox:
        try:
            parts = [float(p) for p in bbox.split(",")]
            if len(parts) != 4:
                raise ValueError
            bbox_tuple = (parts[0], parts[1], parts[2], parts[3])
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid bbox format") from exc

    center = (lat, lon) if lat is not None and lon is not None else None

    pins = fetch_map_projects(
        db,
        bbox=bbox_tuple,
        center=center,
        radius_km=radius_km,
        min_overall_score=min_overall_score,
        project_type=project_type,
        status=status,
    )
    return ProjectMapResponse(items=pins)


@router.get("/{project_id}", response_model=ProjectDetailV2)
def project_detail_endpoint(project_id: int, db=Depends(get_db)):
    project = fetch_project_detail(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


__all__ = ["router"]
