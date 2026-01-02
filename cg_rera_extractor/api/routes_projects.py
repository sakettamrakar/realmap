"""Project-related API routes implementing Phase 6 endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from cg_rera_extractor.api.deps import get_db
from cg_rera_extractor.api.schemas import (
    ProjectDetailV2,
    ProjectDetailV2,
    ProjectMapResponse,
    ProjectSearchResponse,
    ProjectInventoryResponse,
    InventoryStats,
    UnitResponse,
)
from cg_rera_extractor.db import Unit
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
    # Point 24: Tag-based filtering
    tags: list[str] | None = Query(None, description="Filter by tag slugs (e.g., metro-connected, near-it-park)"),
    tags_match_all: bool = Query(False, description="If true, require ALL tags. If false, match ANY tag."),
    # Point 25: RERA verification filter
    rera_verified_only: bool = Query(False, description="Only show RERA-verified projects"),
    group_by_parent: bool = Query(False, description="Group multiple registrations under one parent project"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    sort_by: str = Query("overall_score", pattern="^(overall_score|location_score|amenity_score|value_score|registration_date|distance|price|name)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db=Depends(get_db),
):
    """
    Search projects with advanced filtering.
    
    ## Filter Options
    
    **Location:**
    - `district`, `tehsil`: Filter by location hierarchy
    - `bbox`: Bounding box as "minLat,minLon,maxLat,maxLon"
    - `lat`, `lon`, `radius_km`: Radius search
    
    **Project Attributes:**
    - `project_types`: Filter by type (residential, commercial)
    - `statuses`: Filter by status (registered, completed)
    - `amenities`: Comma-separated onsite amenities
    
    **Scores:**
    - `min_overall_score`, `min_location_score`, `min_amenity_score`: 0-1 range
    
    **Price:**
    - `min_price`, `max_price`: Price range filter
    
    **Tags (Point 24):**
    - `tags`: List of tag slugs for faceted filtering
    - `tags_match_all`: AND vs OR for multiple tags
    
    **Verification (Point 25):**
    - `rera_verified_only`: Only show verified projects
    
    ## Response
    Returns paginated results with discovery metadata (tags, verification status).
    """
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
        tags=tags,
        tags_match_all=tags_match_all,
        rera_verified_only=rera_verified_only,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
        group_by_parent=group_by_parent,
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
    """
    Get project details by internal database ID.
    
    For unified identifier lookup (accepts ID or RERA number),
    use GET /projects/lookup/{identifier} instead.
    """
    project = fetch_project_detail(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/inventory", response_model=ProjectInventoryResponse)
def get_project_inventory(project_id: int, db=Depends(get_db)):
    """
    Get detailed unit inventory for a project.
    """
    from cg_rera_extractor.db import Unit

    units = db.query(Unit).filter(Unit.project_id == project_id).all()

    # Calculate stats
    total = len(units)
    available = sum(1 for u in units if (u.status or "").lower() == "available")
    booked = sum(1 for u in units if (u.status or "").lower() in ["booked", "sold"])
    unknown = total - available - booked

    # Map to response objects with sqft derived if only sqm exists
    unit_responses: list[UnitResponse] = []
    for u in units:
        carpet_area_sqft = None
        if u.carpet_area_sqm:
            carpet_area_sqft = round(u.carpet_area_sqm * 10.7639, 2)

        unit_responses.append(UnitResponse(
            id=u.id,
            block_name=u.block_name,
            floor_no=u.floor_no,
            unit_no=u.unit_no,
            unit_type=u.unit_type,
            carpet_area_sqm=u.carpet_area_sqm,
            carpet_area_sqft=carpet_area_sqft,
            status=u.status,
            raw_data=u.raw_data,
        ))

    return ProjectInventoryResponse(
        stats=InventoryStats(
            total_units=total,
            available_units=available,
            booked_units=booked,
            unknown_units=unknown,
        ),
        units=unit_responses,
    )


@router.get("/lookup/{identifier}")
def unified_project_lookup(
    identifier: str,
    include_hierarchy: bool = Query(
        False,
        description="Include full Project → Tower → Unit hierarchy (SSR optimized)"
    ),
    include_jsonld: bool = Query(
        False,
        description="Include Schema.org JSON-LD for SEO"
    ),
    db=Depends(get_db),
):
    """
    Unified Project Identity API (Point 11).
    
    Accepts EITHER:
    - Internal project ID (numeric): e.g., "123"
    - RERA registration number: e.g., "P51900001234"
    
    ## Features
    - Auto-detects identifier type
    - Optional full hierarchical tree (Project → Tower → Unit)
    - Optional JSON-LD for SSR/SEO
    - Includes data provenance
    
    ## Parameters
    - **identifier**: Project ID (number) or RERA registration number (string)
    - **include_hierarchy**: Include nested buildings/units for SSR
    - **include_jsonld**: Include Schema.org structured data
    
    ## Examples
    ```
    GET /projects/lookup/123
    GET /projects/lookup/P51900001234
    GET /projects/lookup/123?include_hierarchy=true&include_jsonld=true
    ```
    """
    from sqlalchemy.orm import selectinload
    from cg_rera_extractor.db import Project
    from cg_rera_extractor.api.schemas_api import (
        ProjectHierarchy,
        TowerHierarchy,
        DataProvenance,
        ExtractionMethodEnum,
    )
    from cg_rera_extractor.api.services.jsonld import generate_project_jsonld
    
    project = None
    
    # Detect identifier type
    if identifier.isdigit():
        # Numeric - treat as project ID
        project_id = int(identifier)
        project = (
            db.query(Project)
            .options(
                selectinload(Project.buildings),
                selectinload(Project.promoters),
                selectinload(Project.score),
                selectinload(Project.pricing_snapshots),
                selectinload(Project.unit_types),
                selectinload(Project.project_unit_types),
            )
            .filter(Project.id == project_id)
            .first()
        )
    else:
        # Non-numeric - treat as RERA registration number
        project = (
            db.query(Project)
            .options(
                selectinload(Project.buildings),
                selectinload(Project.promoters),
                selectinload(Project.score),
                selectinload(Project.pricing_snapshots),
                selectinload(Project.unit_types),
                selectinload(Project.project_unit_types),
            )
            .filter(Project.rera_registration_number == identifier)
            .first()
        )
        
        # If not found, try case-insensitive search
        if not project:
            project = (
                db.query(Project)
                .options(
                    selectinload(Project.buildings),
                    selectinload(Project.promoters),
                    selectinload(Project.score),
                    selectinload(Project.pricing_snapshots),
                )
                .filter(Project.rera_registration_number.ilike(identifier))
                .first()
            )
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project not found for identifier: {identifier}"
        )
    
    # Build response
    response: dict = {}
    
    # Core project data
    lat = float(project.latitude) if project.latitude else None
    lon = float(project.longitude) if project.longitude else None
    
    developer_name = None
    if project.promoters:
        developer_name = project.promoters[0].promoter_name
    
    # Build towers hierarchy if requested
    towers = []
    if include_hierarchy:
        for building in project.buildings:
            tower = TowerHierarchy(
                id=building.id,
                building_name=building.building_name,
                building_type=building.building_type,
                number_of_floors=building.number_of_floors,
                total_units=building.total_units,
                status=building.status,
                units=[],  # TODO: Populate from Unit table when available
            )
            towers.append(tower)
    
    # Build unit types summary
    unit_types = []
    for ut in project.project_unit_types or []:
        if ut.is_active:
            unit_types.append({
                "label": ut.unit_label,
                "bedrooms": ut.bedrooms,
                "bathrooms": ut.bathrooms,
                "carpet_area_min_sqft": float(ut.carpet_area_min_sqft) if ut.carpet_area_min_sqft else None,
                "carpet_area_max_sqft": float(ut.carpet_area_max_sqft) if ut.carpet_area_max_sqft else None,
            })
    
    # Data provenance
    provenance = DataProvenance(
        last_updated_at=project.scraped_at,
        source_domain="rera.cg.gov.in",
        extraction_method=ExtractionMethodEnum.SCRAPER,
        confidence_score=float(project.geo_confidence) if project.geo_confidence else None,
        data_quality_score=project.data_quality_score,
    )
    
    project_hierarchy = ProjectHierarchy(
        id=project.id,
        rera_id=project.rera_registration_number,
        state_code=project.state_code,
        name=project.project_name,
        status=project.status,
        registration_date=project.approved_date,
        expected_completion=project.proposed_end_date or project.extended_end_date,
        district=project.district,
        tehsil=project.tehsil,
        address=project.full_address or project.normalized_address,
        lat=lat,
        lon=lon,
        developer_id=None,  # TODO: Link when Developer table is populated
        developer_name=developer_name,
        towers=towers if include_hierarchy else [],
        unit_types=unit_types,
        provenance=provenance,
    )
    
    response["project"] = project_hierarchy
    
    # Include JSON-LD if requested
    if include_jsonld:
        # Get pricing info
        pricing = None
        if project.pricing_snapshots:
            active = [s for s in project.pricing_snapshots if s.is_active]
            if active:
                min_prices = [float(s.min_price_total) for s in active if s.min_price_total]
                max_prices = [float(s.max_price_total) for s in active if s.max_price_total]
                pricing = {
                    "min_price_total": min(min_prices) if min_prices else None,
                    "max_price_total": max(max_prices) if max_prices else None,
                }
        
        jsonld = generate_project_jsonld(
            project=project,
            scores=project.score,
            pricing=pricing,
        )
        response["schema_org"] = jsonld.model_dump(by_alias=True, exclude_none=True)
    
    return response


__all__ = ["router"]
