"""
Discovery & Trust Layer Pydantic Schemas (Points 24-26).

This module contains API DTOs for:
- Point 24: Structured Locality Tags (Faceted Search)
- Point 25: RERA Verification System (The Trust Badge)
- Point 26: Entity Enrichment & Knowledge Graph (Landmarks)
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Enums (Mirror of db/enums.py for API layer)
# =============================================================================

class TagCategoryEnum(str, Enum):
    """Tag category for grouping in faceted search UI. (Point 24)"""
    PROXIMITY = "PROXIMITY"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    INVESTMENT = "INVESTMENT"
    LIFESTYLE = "LIFESTYLE"
    CERTIFICATION = "CERTIFICATION"


class ReraVerificationStatusEnum(str, Enum):
    """RERA registration verification status. (Point 25)"""
    VERIFIED = "VERIFIED"
    PENDING = "PENDING"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    NOT_FOUND = "NOT_FOUND"
    UNKNOWN = "UNKNOWN"


# =============================================================================
# Point 24: Tags for Faceted Search
# =============================================================================

class TagBase(BaseModel):
    """Base tag fields."""
    slug: str = Field(..., description="URL-friendly unique identifier")
    name: str = Field(..., description="Human-readable display name")
    description: str | None = None
    category: TagCategoryEnum
    icon_emoji: str | None = None
    color_hex: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    is_featured: bool = False


class TagCreate(TagBase):
    """Schema for creating a tag."""
    is_auto_generated: bool = False
    auto_rule_json: dict[str, Any] | None = None
    sort_order: int = 0
    seo_title: str | None = None
    seo_description: str | None = None


class TagResponse(TagBase):
    """Full tag response for admin/detail views."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_auto_generated: bool = False
    auto_rule_json: dict[str, Any] | None = None
    sort_order: int = 0
    is_active: bool = True
    seo_title: str | None = None
    seo_description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TagSummary(BaseModel):
    """Lightweight tag for list views and filters."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    name: str
    category: TagCategoryEnum
    icon_emoji: str | None = None
    color_hex: str | None = None
    is_featured: bool = False


class TagWithCount(TagSummary):
    """Tag summary with project count (for faceted filter UI)."""
    project_count: int = Field(0, description="Number of projects with this tag")


class TagsByCategory(BaseModel):
    """Grouped tags by category for filter sidebar."""
    category: TagCategoryEnum
    category_label: str = Field(..., description="Human-readable category name")
    tags: list[TagWithCount] = []


class FacetedTagsResponse(BaseModel):
    """Full faceted tags response for search sidebar."""
    categories: list[TagsByCategory] = []
    featured_tags: list[TagWithCount] = Field(
        [], description="High-priority tags to show at top"
    )
    total_tags: int = 0


# =============================================================================
# Project-Tag relationship
# =============================================================================

class ProjectTagAssociation(BaseModel):
    """Association between project and tag with metadata."""
    model_config = ConfigDict(from_attributes=True)
    
    tag_id: int
    tag_slug: str
    tag_name: str
    tag_category: TagCategoryEnum
    is_auto_applied: bool = False
    confidence_score: Decimal | None = None
    computed_distance_km: Decimal | None = None
    applied_at: datetime | None = None


class ProjectTagsResponse(BaseModel):
    """Tags assigned to a project."""
    project_id: int
    tags: list[ProjectTagAssociation] = []
    total_count: int = 0


# =============================================================================
# Point 25: RERA Verification System (The Trust Badge)
# =============================================================================

class ReraVerificationBase(BaseModel):
    """Base RERA verification fields."""
    status: ReraVerificationStatusEnum = ReraVerificationStatusEnum.UNKNOWN
    official_record_url: str | None = Field(
        None, description="Direct URL to government RERA portal page"
    )
    portal_screenshot_url: str | None = None


class ReraVerificationCreate(ReraVerificationBase):
    """Schema for recording a verification."""
    project_id: int
    registered_name_on_portal: str | None = None
    promoter_name_on_portal: str | None = None
    portal_registration_date: datetime | None = None
    portal_expiry_date: datetime | None = None
    verification_method: str | None = None
    discrepancy_notes: str | None = None
    raw_portal_data: dict[str, Any] | None = None


class ReraVerificationResponse(ReraVerificationBase):
    """Full verification record response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    registered_name_on_portal: str | None = None
    promoter_name_on_portal: str | None = None
    portal_registration_date: datetime | None = None
    portal_expiry_date: datetime | None = None
    verified_at: datetime
    verified_by: str | None = None
    verification_method: str | None = None
    has_discrepancies: bool = False
    discrepancy_notes: str | None = None
    is_current: bool = True


class TrustBadge(BaseModel):
    """
    The Trust Badge - simplified verification status for display.
    
    This is the consumer-facing representation of RERA verification.
    """
    status: ReraVerificationStatusEnum
    status_label: str = Field(..., description="Human-readable status label")
    status_color: str = Field(..., description="Color code for badge display")
    is_verified: bool = Field(False, description="Simplified boolean check")
    official_link: str | None = Field(
        None, description="Link to government verification page"
    )
    verified_at: datetime | None = None
    expiry_date: datetime | None = Field(
        None, description="RERA registration expiry date"
    )
    days_until_expiry: int | None = Field(
        None, description="Days until expiry (negative if expired)"
    )
    has_warnings: bool = Field(
        False, description="True if discrepancies or near expiry"
    )
    warning_message: str | None = None

    @classmethod
    def from_verification(
        cls, 
        verification: ReraVerificationResponse | None,
        rera_number: str | None = None
    ) -> "TrustBadge":
        """Create TrustBadge from verification record."""
        if verification is None:
            return cls(
                status=ReraVerificationStatusEnum.UNKNOWN,
                status_label="Not Verified",
                status_color="#9CA3AF",  # gray-400
                is_verified=False,
            )
        
        # Status to display mapping
        status_map = {
            ReraVerificationStatusEnum.VERIFIED: ("Verified", "#10B981", True),  # green-500
            ReraVerificationStatusEnum.PENDING: ("Pending", "#F59E0B", False),  # amber-500
            ReraVerificationStatusEnum.REVOKED: ("Revoked", "#EF4444", False),  # red-500
            ReraVerificationStatusEnum.EXPIRED: ("Expired", "#EF4444", False),  # red-500
            ReraVerificationStatusEnum.NOT_FOUND: ("Not Found", "#EF4444", False),  # red-500
            ReraVerificationStatusEnum.UNKNOWN: ("Not Verified", "#9CA3AF", False),  # gray-400
        }
        
        label, color, is_verified = status_map.get(
            verification.status, 
            ("Unknown", "#9CA3AF", False)
        )
        
        # Calculate days until expiry
        days_until_expiry = None
        has_warnings = False
        warning_message = None
        
        if verification.portal_expiry_date:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            delta = verification.portal_expiry_date - now
            days_until_expiry = delta.days
            
            if days_until_expiry < 0:
                has_warnings = True
                warning_message = "RERA registration has expired"
            elif days_until_expiry < 90:
                has_warnings = True
                warning_message = f"RERA registration expires in {days_until_expiry} days"
        
        if verification.has_discrepancies:
            has_warnings = True
            if warning_message:
                warning_message += "; Data discrepancies detected"
            else:
                warning_message = "Data discrepancies detected"
        
        return cls(
            status=verification.status,
            status_label=label,
            status_color=color,
            is_verified=is_verified,
            official_link=verification.official_record_url,
            verified_at=verification.verified_at,
            expiry_date=verification.portal_expiry_date,
            days_until_expiry=days_until_expiry,
            has_warnings=has_warnings,
            warning_message=warning_message,
        )


# =============================================================================
# Point 26: Landmarks & Entity Linking
# =============================================================================

class LandmarkBase(BaseModel):
    """Base landmark fields."""
    slug: str = Field(..., description="URL-friendly identifier")
    name: str
    alternate_names: list[str] | None = None
    category: str = Field(..., description="Type: mall, tech_park, metro_station, etc.")
    subcategory: str | None = None
    lat: Decimal
    lon: Decimal
    address: str | None = None
    city: str | None = None
    district: str | None = None
    state: str | None = None


class LandmarkCreate(LandmarkBase):
    """Schema for creating a landmark."""
    established_year: int | None = None
    website: str | None = None
    image_url: str | None = None
    description: str | None = None
    importance_score: int = Field(50, ge=0, le=100)
    default_proximity_km: Decimal = Decimal("5.0")
    seo_title: str | None = None
    seo_description: str | None = None


class LandmarkResponse(LandmarkBase):
    """Full landmark response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    established_year: int | None = None
    website: str | None = None
    image_url: str | None = None
    description: str | None = None
    importance_score: int = 50
    default_proximity_km: Decimal = Decimal("5.0")
    seo_title: str | None = None
    seo_description: str | None = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LandmarkSummary(BaseModel):
    """Lightweight landmark for list views."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    name: str
    category: str
    lat: Decimal
    lon: Decimal
    city: str | None = None
    image_url: str | None = None


class LandmarkWithDistance(LandmarkSummary):
    """Landmark with distance info (for project context)."""
    distance_km: Decimal
    driving_time_mins: int | None = None
    walking_time_mins: int | None = None
    is_highlighted: bool = False
    display_label: str | None = Field(
        None, 
        description="e.g., '2.5 km from Phoenix Mall'"
    )


class LandmarksByCategory(BaseModel):
    """Grouped landmarks by category for display."""
    category: str
    category_label: str
    landmarks: list[LandmarkWithDistance] = []


class ProjectLandmarksResponse(BaseModel):
    """All landmarks near a project, grouped by category."""
    project_id: int
    categories: list[LandmarksByCategory] = []
    highlighted: list[LandmarkWithDistance] = Field(
        [], description="Top landmarks to show prominently"
    )
    total_count: int = 0


class NearbyProjectsResponse(BaseModel):
    """Projects near a specific landmark."""
    landmark_id: int
    landmark_name: str
    landmark_slug: str
    projects: list["ProjectNearLandmark"] = []
    total_count: int = 0


class ProjectNearLandmark(BaseModel):
    """Project summary for landmark proximity view."""
    project_id: int
    project_name: str
    rera_number: str | None = None
    distance_km: Decimal
    lat: Decimal
    lon: Decimal
    overall_score: Decimal | None = None
    min_price_total: Decimal | None = None


# =============================================================================
# Combined Discovery Response for Project Detail
# =============================================================================

class ProjectDiscoveryData(BaseModel):
    """
    All discovery data for a project (Points 24-26).
    
    This is embedded in project detail responses to provide:
    - Trust badge (RERA verification)
    - Tags (for filtering/display)
    - Nearby landmarks
    """
    trust_badge: TrustBadge
    tags: list[ProjectTagAssociation] = []
    landmarks: ProjectLandmarksResponse | None = None


# =============================================================================
# Developer Siblings Enhancement (Point 26 extension)
# =============================================================================

class DeveloperSiblingProject(BaseModel):
    """Other project by same developer."""
    project_id: int
    project_name: str
    rera_number: str | None = None
    status: str | None = None
    district: str | None = None
    overall_score: Decimal | None = None
    is_current: bool = Field(
        False, description="True if this is the project being viewed"
    )


class DeveloperWithProjects(BaseModel):
    """Developer info with their other projects."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    legal_name: str | None = None
    trust_score: float | None = None
    logo_url: str | None = None
    website: str | None = None
    total_projects: int = 0
    sibling_projects: list[DeveloperSiblingProject] = []


# =============================================================================
# Module exports
# =============================================================================

__all__ = [
    # Enums
    "TagCategoryEnum",
    "ReraVerificationStatusEnum",
    
    # Point 24: Tags
    "TagBase",
    "TagCreate",
    "TagResponse",
    "TagSummary",
    "TagWithCount",
    "TagsByCategory",
    "FacetedTagsResponse",
    "ProjectTagAssociation",
    "ProjectTagsResponse",
    
    # Point 25: RERA Verification
    "ReraVerificationBase",
    "ReraVerificationCreate",
    "ReraVerificationResponse",
    "TrustBadge",
    
    # Point 26: Landmarks
    "LandmarkBase",
    "LandmarkCreate",
    "LandmarkResponse",
    "LandmarkSummary",
    "LandmarkWithDistance",
    "LandmarksByCategory",
    "ProjectLandmarksResponse",
    "NearbyProjectsResponse",
    "ProjectNearLandmark",
    
    # Combined
    "ProjectDiscoveryData",
    
    # Developer siblings
    "DeveloperSiblingProject",
    "DeveloperWithProjects",
]
