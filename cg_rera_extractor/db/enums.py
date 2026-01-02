"""Enumerations for the data model."""
from __future__ import annotations

import enum


class AreaUnit(str, enum.Enum):
    """Canonical area unit for consistent calculations. (Enhancement #3)"""
    SQFT = "SQFT"
    SQM = "SQM"


class ProjectPhase(str, enum.Enum):
    """Project lifecycle phase. (Enhancement #5)"""
    PRE_LAUNCH = "PRE_LAUNCH"
    UNDER_CONSTRUCTION = "UNDER_CONSTRUCTION"
    READY_TO_MOVE = "READY_TO_MOVE"
    COMPLETED = "COMPLETED"


class AmenityCategoryType(str, enum.Enum):
    """Top-level amenity category. (Enhancement #7)"""
    HEALTH = "HEALTH"
    LEISURE = "LEISURE"
    CONVENIENCE = "CONVENIENCE"
    CONNECTIVITY = "CONNECTIVITY"
    SECURITY = "SECURITY"
    ENVIRONMENT = "ENVIRONMENT"
    SOCIAL = "SOCIAL"


class UnitStatus(str, enum.Enum):
    """Status of an individual unit. (Enhancement #2)"""
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"
    SOLD = "SOLD"
    UNDER_CONSTRUCTION = "UNDER_CONSTRUCTION"
    READY = "READY"


# =============================================================================
# Point 24: Tag Category for Faceted Search
# =============================================================================

class TagCategory(str, enum.Enum):
    """Category of project tags for faceted search. (Point 24)"""
    PROXIMITY = "PROXIMITY"         # e.g., "Hinjewadi-proximate", "Near-Airport"
    INFRASTRUCTURE = "INFRASTRUCTURE"  # e.g., "Metro-connected", "Highway-access"
    INVESTMENT = "INVESTMENT"       # e.g., "High-Rental-Yield", "Pre-Launch"
    LIFESTYLE = "LIFESTYLE"         # e.g., "Gated-Community", "Waterfront"
    CERTIFICATION = "CERTIFICATION" # e.g., "IGBC-Green", "RERA-Verified"


# =============================================================================
# Point 25: RERA Verification Status
# =============================================================================

class ReraVerificationStatus(str, enum.Enum):
    """RERA registration verification status. (Point 25)"""
    VERIFIED = "VERIFIED"       # Confirmed active on government portal
    PENDING = "PENDING"         # Awaiting verification
    REVOKED = "REVOKED"         # Registration cancelled by authority
    EXPIRED = "EXPIRED"         # Registration period ended
    NOT_FOUND = "NOT_FOUND"     # Could not locate on portal
    UNKNOWN = "UNKNOWN"         # Not yet checked


class MediaCategory(str, enum.Enum):
    """Category of project media assets. (Phase 1)"""
    GALLERY = "GALLERY"
    FLOOR_PLAN = "FLOOR_PLAN"
    VIDEO = "VIDEO"
    VIRTUAL_TOUR = "VIRTUAL_TOUR"
    BROCHURE = "BROCHURE"
    OTHER = "OTHER"


__all__ = [
    "AreaUnit",
    "ProjectPhase",
    "AmenityCategoryType",
    "UnitStatus",
    "TagCategory",
    "ReraVerificationStatus",
    "MediaCategory",
]
