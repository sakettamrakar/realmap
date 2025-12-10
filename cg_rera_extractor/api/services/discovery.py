"""
Discovery & Trust Layer Service Functions (Points 24-26).

This module provides service functions for:
- Point 24: Tag queries and faceted search filtering
- Point 25: RERA verification status lookup
- Point 26: Landmark queries and proximity search
"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cg_rera_extractor.db import Project
from cg_rera_extractor.db.models_discovery import (
    Landmark,
    ProjectLandmark,
    ProjectTag,
    ReraVerification,
    Tag,
)
from cg_rera_extractor.db.enums import TagCategory, ReraVerificationStatus
from cg_rera_extractor.api.schemas_discovery import (
    FacetedTagsResponse,
    LandmarksByCategory,
    LandmarkWithDistance,
    ProjectDiscoveryData,
    ProjectLandmarksResponse,
    ProjectTagAssociation,
    ReraVerificationResponse,
    TagsByCategory,
    TagWithCount,
    TrustBadge,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Point 24: Tag Services
# =============================================================================

def get_all_tags(
    session: Session,
    *,
    active_only: bool = True,
    category: TagCategory | None = None,
) -> list[Tag]:
    """
    Get all tags, optionally filtered by category.
    
    Args:
        session: Database session
        active_only: Only return active tags
        category: Filter by specific category
    
    Returns:
        List of Tag entities
    """
    query = select(Tag).order_by(Tag.sort_order, Tag.name)
    
    if active_only:
        query = query.where(Tag.is_active == True)
    
    if category:
        query = query.where(Tag.category == category)
    
    result = session.execute(query)
    return list(result.scalars().all())


def get_tags_with_counts(
    session: Session,
    *,
    active_only: bool = True,
) -> list[TagWithCount]:
    """
    Get all active tags with project counts.
    
    This is used for faceted search sidebar to show available filters.
    """
    # Join tags with project_tags to count projects
    query = (
        select(
            Tag,
            func.count(ProjectTag.project_id).label("project_count")
        )
        .outerjoin(ProjectTag, ProjectTag.tag_id == Tag.id)
        .group_by(Tag.id)
        .order_by(Tag.sort_order, Tag.name)
    )
    
    if active_only:
        query = query.where(Tag.is_active == True)
    
    result = session.execute(query)
    
    tags_with_counts = []
    for tag, count in result:
        tags_with_counts.append(
            TagWithCount(
                id=tag.id,
                slug=tag.slug,
                name=tag.name,
                category=tag.category,
                icon_emoji=tag.icon_emoji,
                color_hex=tag.color_hex,
                is_featured=tag.is_featured,
                project_count=count or 0,
            )
        )
    
    return tags_with_counts


def get_faceted_tags(session: Session) -> FacetedTagsResponse:
    """
    Get tags organized by category for faceted search UI.
    
    Returns tags grouped by category with counts, plus featured tags.
    """
    all_tags = get_tags_with_counts(session)
    
    # Group by category
    category_map: dict[TagCategory, list[TagWithCount]] = {}
    featured: list[TagWithCount] = []
    
    for tag in all_tags:
        if tag.is_featured:
            featured.append(tag)
        
        if tag.category not in category_map:
            category_map[tag.category] = []
        category_map[tag.category].append(tag)
    
    # Build category groups
    category_labels = {
        TagCategory.PROXIMITY: "Location & Proximity",
        TagCategory.INFRASTRUCTURE: "Infrastructure",
        TagCategory.INVESTMENT: "Investment Highlights",
        TagCategory.LIFESTYLE: "Lifestyle",
        TagCategory.CERTIFICATION: "Certifications",
    }
    
    categories = [
        TagsByCategory(
            category=cat,
            category_label=category_labels.get(cat, cat.value),
            tags=tags,
        )
        for cat, tags in category_map.items()
    ]
    
    # Sort categories in preferred order
    category_order = [
        TagCategory.PROXIMITY,
        TagCategory.INFRASTRUCTURE,
        TagCategory.INVESTMENT,
        TagCategory.LIFESTYLE,
        TagCategory.CERTIFICATION,
    ]
    categories.sort(key=lambda c: category_order.index(c.category) if c.category in category_order else 99)
    
    return FacetedTagsResponse(
        categories=categories,
        featured_tags=featured,
        total_tags=len(all_tags),
    )


def get_project_tags(
    session: Session,
    project_id: int,
) -> list[ProjectTagAssociation]:
    """
    Get all tags assigned to a project.
    """
    query = (
        select(ProjectTag, Tag)
        .join(Tag, Tag.id == ProjectTag.tag_id)
        .where(ProjectTag.project_id == project_id)
        .where(Tag.is_active == True)
        .order_by(Tag.sort_order, Tag.name)
    )
    
    result = session.execute(query)
    
    associations = []
    for pt, tag in result:
        associations.append(
            ProjectTagAssociation(
                tag_id=tag.id,
                tag_slug=tag.slug,
                tag_name=tag.name,
                tag_category=tag.category,
                is_auto_applied=pt.is_auto_applied,
                confidence_score=pt.confidence_score,
                computed_distance_km=pt.computed_distance_km,
                applied_at=pt.applied_at,
            )
        )
    
    return associations


def get_projects_by_tags(
    session: Session,
    tag_slugs: list[str],
    *,
    match_all: bool = False,
) -> list[int]:
    """
    Get project IDs that have specified tags.
    
    Args:
        session: Database session
        tag_slugs: List of tag slugs to filter by
        match_all: If True, require ALL tags. If False, require ANY tag.
    
    Returns:
        List of project IDs matching the filter
    """
    if not tag_slugs:
        return []
    
    # Get tag IDs
    tag_query = select(Tag.id).where(Tag.slug.in_(tag_slugs))
    tag_ids = [row[0] for row in session.execute(tag_query)]
    
    if not tag_ids:
        return []
    
    if match_all:
        # Projects must have ALL specified tags
        query = (
            select(ProjectTag.project_id)
            .where(ProjectTag.tag_id.in_(tag_ids))
            .group_by(ProjectTag.project_id)
            .having(func.count(ProjectTag.tag_id) == len(tag_ids))
        )
    else:
        # Projects with ANY of the specified tags
        query = (
            select(ProjectTag.project_id)
            .where(ProjectTag.tag_id.in_(tag_ids))
            .distinct()
        )
    
    result = session.execute(query)
    return [row[0] for row in result]


# =============================================================================
# Point 25: RERA Verification Services
# =============================================================================

def get_project_verification(
    session: Session,
    project_id: int,
) -> ReraVerification | None:
    """
    Get current RERA verification status for a project.
    """
    query = (
        select(ReraVerification)
        .where(ReraVerification.project_id == project_id)
        .where(ReraVerification.is_current == True)
        .order_by(ReraVerification.verified_at.desc())
        .limit(1)
    )
    
    result = session.execute(query)
    return result.scalar_one_or_none()


def get_project_trust_badge(
    session: Session,
    project_id: int,
    rera_number: str | None = None,
) -> TrustBadge:
    """
    Get trust badge for a project.
    
    This creates a user-friendly representation of RERA verification status.
    """
    verification = get_project_verification(session, project_id)
    
    if verification:
        response = ReraVerificationResponse.model_validate(verification)
        return TrustBadge.from_verification(response, rera_number)
    
    return TrustBadge.from_verification(None, rera_number)


def get_verification_history(
    session: Session,
    project_id: int,
    *,
    limit: int = 10,
) -> list[ReraVerification]:
    """
    Get verification history for a project.
    """
    query = (
        select(ReraVerification)
        .where(ReraVerification.project_id == project_id)
        .order_by(ReraVerification.verified_at.desc())
        .limit(limit)
    )
    
    result = session.execute(query)
    return list(result.scalars().all())


def create_verification_record(
    session: Session,
    project_id: int,
    status: ReraVerificationStatus,
    *,
    official_record_url: str | None = None,
    registered_name_on_portal: str | None = None,
    promoter_name_on_portal: str | None = None,
    portal_registration_date: datetime | None = None,
    portal_expiry_date: datetime | None = None,
    verification_method: str | None = None,
    has_discrepancies: bool = False,
    discrepancy_notes: str | None = None,
    raw_portal_data: dict[str, Any] | None = None,
    verified_by: str | None = "system",
) -> ReraVerification:
    """
    Create a new verification record for a project.
    
    This marks any existing records as not current.
    """
    # Mark existing records as not current
    session.execute(
        select(ReraVerification)
        .where(ReraVerification.project_id == project_id)
        .where(ReraVerification.is_current == True)
    )
    for old_record in session.query(ReraVerification).filter(
        ReraVerification.project_id == project_id,
        ReraVerification.is_current == True
    ):
        old_record.is_current = False
    
    # Create new record
    verification = ReraVerification(
        project_id=project_id,
        status=status,
        official_record_url=official_record_url,
        registered_name_on_portal=registered_name_on_portal,
        promoter_name_on_portal=promoter_name_on_portal,
        portal_registration_date=portal_registration_date,
        portal_expiry_date=portal_expiry_date,
        verification_method=verification_method,
        has_discrepancies=has_discrepancies,
        discrepancy_notes=discrepancy_notes,
        raw_portal_data=raw_portal_data,
        verified_by=verified_by,
        is_current=True,
    )
    
    session.add(verification)
    session.flush()
    
    return verification


# =============================================================================
# Point 26: Landmark Services
# =============================================================================

def get_landmark_by_slug(
    session: Session,
    slug: str,
) -> Landmark | None:
    """Get landmark by slug."""
    query = select(Landmark).where(Landmark.slug == slug)
    result = session.execute(query)
    return result.scalar_one_or_none()


def get_landmarks_by_category(
    session: Session,
    category: str,
    *,
    city: str | None = None,
    active_only: bool = True,
) -> list[Landmark]:
    """Get landmarks filtered by category and optionally city."""
    query = select(Landmark).where(Landmark.category == category)
    
    if active_only:
        query = query.where(Landmark.is_active == True)
    
    if city:
        query = query.where(Landmark.city == city)
    
    query = query.order_by(Landmark.importance_score.desc(), Landmark.name)
    
    result = session.execute(query)
    return list(result.scalars().all())


def get_project_landmarks(
    session: Session,
    project_id: int,
    *,
    max_distance_km: float | None = None,
    limit: int | None = None,
) -> ProjectLandmarksResponse:
    """
    Get all landmarks near a project, grouped by category.
    """
    query = (
        select(ProjectLandmark, Landmark)
        .join(Landmark, Landmark.id == ProjectLandmark.landmark_id)
        .where(ProjectLandmark.project_id == project_id)
        .where(Landmark.is_active == True)
        .order_by(ProjectLandmark.distance_km)
    )
    
    if max_distance_km is not None:
        query = query.where(ProjectLandmark.distance_km <= max_distance_km)
    
    if limit is not None:
        query = query.limit(limit)
    
    result = session.execute(query)
    
    # Group by category
    category_map: dict[str, list[LandmarkWithDistance]] = {}
    highlighted: list[LandmarkWithDistance] = []
    total = 0
    
    for pl, landmark in result:
        total += 1
        
        lwd = LandmarkWithDistance(
            id=landmark.id,
            slug=landmark.slug,
            name=landmark.name,
            category=landmark.category,
            lat=landmark.lat,
            lon=landmark.lon,
            city=landmark.city,
            image_url=landmark.image_url,
            distance_km=pl.distance_km,
            driving_time_mins=pl.driving_time_mins,
            walking_time_mins=pl.walking_time_mins,
            is_highlighted=pl.is_highlighted,
            display_label=f"{pl.distance_km:.1f} km from {landmark.name}",
        )
        
        if pl.is_highlighted:
            highlighted.append(lwd)
        
        if landmark.category not in category_map:
            category_map[landmark.category] = []
        category_map[landmark.category].append(lwd)
    
    # Build categories
    category_labels = {
        "mall": "Shopping Malls",
        "tech_park": "IT Parks & Tech Hubs",
        "metro_station": "Metro Stations",
        "railway_station": "Railway Stations",
        "airport": "Airports",
        "hospital": "Hospitals",
        "school": "Schools & Universities",
        "bus_stand": "Bus Stations",
    }
    
    categories = [
        LandmarksByCategory(
            category=cat,
            category_label=category_labels.get(cat, cat.replace("_", " ").title()),
            landmarks=landmarks,
        )
        for cat, landmarks in category_map.items()
    ]
    
    return ProjectLandmarksResponse(
        project_id=project_id,
        categories=categories,
        highlighted=highlighted,
        total_count=total,
    )


def get_projects_near_landmark(
    session: Session,
    landmark_id: int,
    *,
    max_distance_km: float = 10.0,
    limit: int = 50,
) -> list[tuple[int, Decimal]]:
    """
    Get project IDs and distances near a landmark.
    
    Returns list of (project_id, distance_km) tuples.
    """
    query = (
        select(ProjectLandmark.project_id, ProjectLandmark.distance_km)
        .where(ProjectLandmark.landmark_id == landmark_id)
        .where(ProjectLandmark.distance_km <= max_distance_km)
        .order_by(ProjectLandmark.distance_km)
        .limit(limit)
    )
    
    result = session.execute(query)
    return [(row[0], row[1]) for row in result]


# =============================================================================
# Combined Discovery Data
# =============================================================================

def get_project_discovery_data(
    session: Session,
    project_id: int,
    rera_number: str | None = None,
) -> ProjectDiscoveryData:
    """
    Get all discovery data for a project.
    
    This combines:
    - Trust badge (RERA verification)
    - Tags
    - Nearby landmarks
    """
    trust_badge = get_project_trust_badge(session, project_id, rera_number)
    tags = get_project_tags(session, project_id)
    landmarks = get_project_landmarks(session, project_id, max_distance_km=10.0)
    
    return ProjectDiscoveryData(
        trust_badge=trust_badge,
        tags=tags,
        landmarks=landmarks if landmarks.total_count > 0 else None,
    )


# =============================================================================
# Developer Siblings
# =============================================================================

def get_developer_sibling_projects(
    session: Session,
    project_id: int,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Get other projects by the same developer.
    
    Returns lightweight project summaries for the developer's portfolio.
    """
    from cg_rera_extractor.db.models_enhanced import DeveloperProject
    
    # First, find the developer(s) for this project
    dev_query = (
        select(DeveloperProject.developer_id)
        .where(DeveloperProject.project_id == project_id)
    )
    dev_result = session.execute(dev_query)
    developer_ids = [row[0] for row in dev_result]
    
    if not developer_ids:
        return []
    
    # Get other projects by same developer(s)
    sibling_query = (
        select(
            Project.id,
            Project.project_name,
            Project.rera_registration_number,
            Project.status,
            Project.district,
        )
        .join(DeveloperProject, DeveloperProject.project_id == Project.id)
        .where(DeveloperProject.developer_id.in_(developer_ids))
        .where(Project.id != project_id)
        .distinct()
        .limit(limit)
    )
    
    result = session.execute(sibling_query)
    
    siblings = []
    for row in result:
        siblings.append({
            "project_id": row[0],
            "project_name": row[1],
            "rera_number": row[2],
            "status": row[3],
            "district": row[4],
            "is_current": False,
        })
    
    return siblings


__all__ = [
    # Tag services
    "get_all_tags",
    "get_tags_with_counts",
    "get_faceted_tags",
    "get_project_tags",
    "get_projects_by_tags",
    
    # RERA verification services
    "get_project_verification",
    "get_project_trust_badge",
    "get_verification_history",
    "create_verification_record",
    
    # Landmark services
    "get_landmark_by_slug",
    "get_landmarks_by_category",
    "get_project_landmarks",
    "get_projects_near_landmark",
    
    # Combined
    "get_project_discovery_data",
    
    # Developer siblings
    "get_developer_sibling_projects",
]
