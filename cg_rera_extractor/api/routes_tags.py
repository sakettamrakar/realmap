"""
Discovery & Trust Layer API Routes (Points 24-26).

This module provides endpoints for:
- Point 24: Tag listing and faceted search filters
- Point 25: RERA verification status
- Point 26: Landmark queries
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from cg_rera_extractor.api.deps import get_db
from cg_rera_extractor.api.schemas_discovery import (
    FacetedTagsResponse,
    LandmarkResponse,
    LandmarkSummary,
    NearbyProjectsResponse,
    ProjectDiscoveryData,
    ProjectLandmarksResponse,
    ProjectNearLandmark,
    ProjectTagsResponse,
    ReraVerificationResponse,
    TagResponse,
    TrustBadge,
)
from cg_rera_extractor.api.services.discovery import (
    get_all_tags,
    get_faceted_tags,
    get_landmark_by_slug,
    get_project_discovery_data,
    get_project_landmarks,
    get_project_tags,
    get_project_trust_badge,
    get_project_verification,
    get_projects_near_landmark,
    get_verification_history,
)
from cg_rera_extractor.db import Project
from cg_rera_extractor.db.models_discovery import Landmark

router = APIRouter(prefix="/discovery", tags=["discovery-trust"])


# =============================================================================
# Point 24: Tag Endpoints
# =============================================================================

@router.get("/tags", response_model=list[TagResponse])
def list_tags(
    session: Annotated[Session, Depends(get_db)],
    active_only: bool = Query(True, description="Only return active tags"),
    category: str | None = Query(None, description="Filter by category slug"),
):
    """
    List all available tags.
    
    Tags are used for faceted search filtering. Each tag belongs to a category
    like PROXIMITY, INFRASTRUCTURE, INVESTMENT, LIFESTYLE, or CERTIFICATION.
    """
    from cg_rera_extractor.db.enums import TagCategory
    
    cat_enum = None
    if category:
        try:
            cat_enum = TagCategory(category.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {category}. Valid values: {[c.value for c in TagCategory]}"
            )
    
    tags = get_all_tags(session, active_only=active_only, category=cat_enum)
    return [TagResponse.model_validate(t) for t in tags]


@router.get("/tags/faceted", response_model=FacetedTagsResponse)
def get_faceted_search_tags(
    session: Annotated[Session, Depends(get_db)],
):
    """
    Get tags organized for faceted search UI.
    
    Returns tags grouped by category with project counts.
    Includes a list of featured tags to display prominently.
    
    ## Example Response Structure
    ```json
    {
      "categories": [
        {
          "category": "PROXIMITY",
          "category_label": "Location & Proximity",
          "tags": [
            {"slug": "metro-connected", "name": "Metro Connected", "project_count": 45},
            {"slug": "near-it-park", "name": "Near IT Park", "project_count": 32}
          ]
        }
      ],
      "featured_tags": [...],
      "total_tags": 25
    }
    ```
    """
    return get_faceted_tags(session)


@router.get("/projects/{project_id}/tags", response_model=ProjectTagsResponse)
def get_project_tag_list(
    session: Annotated[Session, Depends(get_db)],
    project_id: int = Path(..., description="Project ID"),
):
    """
    Get all tags assigned to a specific project.
    
    Each tag includes metadata like whether it was auto-applied
    and any computed values (e.g., distance for proximity tags).
    """
    tags = get_project_tags(session, project_id)
    return ProjectTagsResponse(
        project_id=project_id,
        tags=tags,
        total_count=len(tags),
    )


# =============================================================================
# Point 25: RERA Verification Endpoints
# =============================================================================

@router.get("/projects/{project_id}/verification", response_model=ReraVerificationResponse | None)
def get_verification_status(
    session: Annotated[Session, Depends(get_db)],
    project_id: int = Path(..., description="Project ID"),
):
    """
    Get current RERA verification status for a project.
    
    Returns the most recent verification record with full details.
    """
    verification = get_project_verification(session, project_id)
    if verification:
        return ReraVerificationResponse.model_validate(verification)
    return None


@router.get("/projects/{project_id}/trust-badge", response_model=TrustBadge)
def get_trust_badge(
    session: Annotated[Session, Depends(get_db)],
    project_id: int = Path(..., description="Project ID"),
):
    """
    Get Trust Badge for a project.
    
    The Trust Badge is a simplified, user-friendly representation of
    RERA verification status with:
    - Status label and color
    - Link to official government page
    - Expiry warning if applicable
    - Warning flags for discrepancies
    
    ## Status Colors
    - VERIFIED: Green (#10B981)
    - PENDING: Amber (#F59E0B)
    - REVOKED/EXPIRED/NOT_FOUND: Red (#EF4444)
    - UNKNOWN: Gray (#9CA3AF)
    """
    # Get project's RERA number for context
    project = session.get(Project, project_id)
    rera_number = project.rera_registration_number if project else None
    
    return get_project_trust_badge(session, project_id, rera_number)


@router.get("/projects/{project_id}/verification/history", response_model=list[ReraVerificationResponse])
def get_verification_history_endpoint(
    session: Annotated[Session, Depends(get_db)],
    project_id: int = Path(..., description="Project ID"),
    limit: int = Query(10, ge=1, le=100, description="Max records to return"),
):
    """
    Get verification history for a project.
    
    Returns all verification records ordered by date (newest first).
    Useful for audit trails and tracking status changes over time.
    """
    history = get_verification_history(session, project_id, limit=limit)
    return [ReraVerificationResponse.model_validate(v) for v in history]


# =============================================================================
# Point 26: Landmark Endpoints
# =============================================================================

@router.get("/landmarks", response_model=list[LandmarkSummary])
def list_landmarks(
    session: Annotated[Session, Depends(get_db)],
    category: str | None = Query(None, description="Filter by category (mall, tech_park, metro_station, etc.)"),
    city: str | None = Query(None, description="Filter by city"),
    limit: int = Query(100, ge=1, le=500),
):
    """
    List landmarks, optionally filtered by category and city.
    
    ## Categories
    - `mall`: Shopping malls
    - `tech_park`: IT parks and tech hubs
    - `metro_station`: Metro stations
    - `railway_station`: Railway stations
    - `airport`: Airports
    - `hospital`: Hospitals
    - `school`: Schools and universities
    - `bus_stand`: Bus stations
    """
    from sqlalchemy import select
    
    query = select(Landmark).where(Landmark.is_active == True)
    
    if category:
        query = query.where(Landmark.category == category)
    if city:
        query = query.where(Landmark.city == city)
    
    query = query.order_by(Landmark.importance_score.desc()).limit(limit)
    
    result = session.execute(query)
    landmarks = result.scalars().all()
    
    return [LandmarkSummary.model_validate(lm) for lm in landmarks]


@router.get("/landmarks/{slug}", response_model=LandmarkResponse)
def get_landmark_detail(
    session: Annotated[Session, Depends(get_db)],
    slug: str = Path(..., description="Landmark slug"),
):
    """
    Get detailed information about a specific landmark.
    """
    landmark = get_landmark_by_slug(session, slug)
    if not landmark:
        raise HTTPException(status_code=404, detail="Landmark not found")
    
    return LandmarkResponse.model_validate(landmark)


@router.get("/landmarks/{slug}/projects", response_model=NearbyProjectsResponse)
def get_projects_near_landmark_endpoint(
    session: Annotated[Session, Depends(get_db)],
    slug: str = Path(..., description="Landmark slug"),
    max_distance_km: float = Query(10.0, ge=0.1, le=50.0, description="Maximum distance in km"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Get projects near a specific landmark.
    
    Useful for location-based discovery like:
    - "Projects near Hinjewadi IT Park"
    - "Apartments near Metro Station"
    """
    landmark = get_landmark_by_slug(session, slug)
    if not landmark:
        raise HTTPException(status_code=404, detail="Landmark not found")
    
    # Get project IDs and distances
    project_distances = get_projects_near_landmark(
        session, 
        landmark.id, 
        max_distance_km=max_distance_km,
        limit=limit,
    )
    
    # Fetch project details
    from cg_rera_extractor.db import ProjectScores
    from sqlalchemy import select
    
    projects = []
    for project_id, distance_km in project_distances:
        project = session.get(Project, project_id)
        if project:
            # Get score
            score_query = select(ProjectScores.overall_score).where(ProjectScores.project_id == project_id)
            score_result = session.execute(score_query).scalar_one_or_none()
            
            projects.append(
                ProjectNearLandmark(
                    project_id=project.id,
                    project_name=project.project_name,
                    rera_number=project.rera_registration_number,
                    distance_km=distance_km,
                    lat=project.latitude or 0,
                    lon=project.longitude or 0,
                    overall_score=score_result,
                    min_price_total=None,  # Could add price lookup
                )
            )
    
    return NearbyProjectsResponse(
        landmark_id=landmark.id,
        landmark_name=landmark.name,
        landmark_slug=landmark.slug,
        projects=projects,
        total_count=len(projects),
    )


@router.get("/projects/{project_id}/landmarks", response_model=ProjectLandmarksResponse)
def get_project_nearby_landmarks(
    session: Annotated[Session, Depends(get_db)],
    project_id: int = Path(..., description="Project ID"),
    max_distance_km: float = Query(10.0, ge=0.1, le=50.0, description="Maximum distance in km"),
):
    """
    Get all landmarks near a project, grouped by category.
    
    Includes:
    - Distance to each landmark
    - Driving/walking time estimates (if available)
    - Highlighted landmarks for prominent display
    """
    return get_project_landmarks(session, project_id, max_distance_km=max_distance_km)


# =============================================================================
# Combined Discovery Endpoint
# =============================================================================

@router.get("/projects/{project_id}/full", response_model=ProjectDiscoveryData)
def get_full_discovery_data(
    session: Annotated[Session, Depends(get_db)],
    project_id: int = Path(..., description="Project ID"),
):
    """
    Get all discovery data for a project in one call.
    
    Combines:
    - Trust Badge (RERA verification status)
    - Tags (for filtering/display)
    - Nearby Landmarks
    
    This is the recommended endpoint for project detail pages
    to get all discovery/trust data in a single request.
    """
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return get_project_discovery_data(
        session, 
        project_id, 
        project.rera_registration_number,
    )


# Export router
__all__ = ["router"]
