"""
Enhanced Pydantic schemas for the 10-Point Enhancement Standard.

This module contains NEW API DTOs added to meet the enhancement requirements.
These should be imported alongside the existing schemas.py.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Enums (Mirror of db/enums.py for API layer)
# =============================================================================

class AreaUnitEnum(str, Enum):
    """Canonical area unit. (Enhancement #3)"""
    SQFT = "SQFT"
    SQM = "SQM"


class ProjectPhaseEnum(str, Enum):
    """Project lifecycle phase. (Enhancement #5)"""
    PRE_LAUNCH = "PRE_LAUNCH"
    UNDER_CONSTRUCTION = "UNDER_CONSTRUCTION"
    READY_TO_MOVE = "READY_TO_MOVE"
    COMPLETED = "COMPLETED"


class UnitStatusEnum(str, Enum):
    """Status of an individual unit. (Enhancement #2)"""
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"
    SOLD = "SOLD"
    UNDER_CONSTRUCTION = "UNDER_CONSTRUCTION"
    READY = "READY"


class AmenityCategoryEnum(str, Enum):
    """Top-level amenity category. (Enhancement #7)"""
    HEALTH = "HEALTH"
    LEISURE = "LEISURE"
    CONVENIENCE = "CONVENIENCE"
    CONNECTIVITY = "CONNECTIVITY"
    SECURITY = "SECURITY"
    ENVIRONMENT = "ENVIRONMENT"
    SOCIAL = "SOCIAL"


# =============================================================================
# Enhancement #1: Developer Identity
# =============================================================================

class DeveloperBase(BaseModel):
    """Base developer fields."""
    name: str
    state_code: str | None = None
    legal_name: str | None = None
    estd_year: int | None = Field(None, description="Year of establishment")
    trust_score: float | None = Field(None, ge=0, le=10, description="Trust score 0-10")
    total_delivered_sqft: float | None = None
    total_projects_completed: int | None = None
    total_projects_ongoing: int | None = None
    headquarters_city: str | None = None
    website: str | None = None
    logo_url: str | None = None
    description: str | None = None


class DeveloperCreate(DeveloperBase):
    """Schema for creating a developer."""
    pass


class DeveloperResponse(DeveloperBase):
    """Schema for developer API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DeveloperSummary(BaseModel):
    """Lightweight developer projection for list views."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    trust_score: float | None = None
    total_projects_completed: int | None = None
    logo_url: str | None = None


# =============================================================================
# Enhancement #2: Unit Hierarchy
# =============================================================================

class UnitBase(BaseModel):
    """Base unit fields."""
    unit_number: str
    floor_number: int | None = None
    wing: str | None = None
    
    # Area measurements (Enhancement #3 alignment)
    carpet_area_sqft: float | None = None
    builtup_area_sqft: float | None = None
    super_builtup_area_sqft: float | None = None
    
    # Status
    status: UnitStatusEnum | None = UnitStatusEnum.AVAILABLE
    is_corner_unit: bool | None = None
    facing_direction: str | None = None
    
    # Pricing (Enhancement #4 alignment)
    base_price: float | None = None
    price_per_sqft_carpet: float | None = None
    price_per_sqft_sbua: float | None = None


class UnitCreate(UnitBase):
    """Schema for creating a unit."""
    building_id: int
    unit_type_id: int | None = None


class UnitResponse(UnitBase):
    """Schema for unit API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    building_id: int
    unit_type_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UnitSummary(BaseModel):
    """Lightweight unit projection."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    unit_number: str
    floor_number: int | None = None
    status: str | None = None
    carpet_area_sqft: float | None = None
    base_price: float | None = None


# =============================================================================
# Enhancement #3: Area Normalization
# =============================================================================

class NormalizedArea(BaseModel):
    """Normalized area measurements with explicit types."""
    carpet_area: float | None = Field(None, description="Carpet area (inner usable)")
    builtup_area: float | None = Field(None, description="Builtup area (carpet + walls)")
    super_builtup_area: float | None = Field(None, description="Super builtup (includes common areas)")
    unit: AreaUnitEnum = Field(AreaUnitEnum.SQFT, description="Area unit")
    
    @property
    def loading_factor(self) -> float | None:
        """Calculate loading factor (SBUA / Carpet ratio)."""
        if self.carpet_area and self.super_builtup_area and self.carpet_area > 0:
            return self.super_builtup_area / self.carpet_area
        return None


# =============================================================================
# Enhancement #4: Price Per Sqft by Area Type
# =============================================================================

class PricingByAreaType(BaseModel):
    """Price information normalized by area type."""
    # Generic (backward compatible)
    min_price_total: float | None = None
    max_price_total: float | None = None
    min_price_per_sqft: float | None = None
    max_price_per_sqft: float | None = None
    
    # Enhancement #4: Per area type
    price_per_sqft_carpet_min: float | None = Field(None, description="Min price/sqft on carpet area")
    price_per_sqft_carpet_max: float | None = Field(None, description="Max price/sqft on carpet area")
    price_per_sqft_sbua_min: float | None = Field(None, description="Min price/sqft on super builtup")
    price_per_sqft_sbua_max: float | None = Field(None, description="Max price/sqft on super builtup")


# =============================================================================
# Enhancement #5: Structured Possession Timeline
# =============================================================================

class PossessionTimelineBase(BaseModel):
    """Structured possession timeline."""
    marketing_target: date | None = Field(None, description="Date promised by sales")
    regulatory_deadline: date | None = Field(None, description="Legal deadline")
    rera_deadline: date | None = Field(None, description="RERA registered deadline")
    actual_completion: date | None = Field(None, description="Actual completion (if done)")
    phase: ProjectPhaseEnum | None = ProjectPhaseEnum.UNDER_CONSTRUCTION
    phase_start_date: date | None = None
    delay_months: int | None = Field(None, description="Delay from RERA deadline")
    delay_reason: str | None = None
    notes: str | None = None


class PossessionTimelineCreate(PossessionTimelineBase):
    """Schema for creating possession timeline."""
    project_id: int
    building_id: int | None = None


class PossessionTimelineResponse(PossessionTimelineBase):
    """Schema for possession timeline API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    building_id: int | None = None
    created_at: datetime | None = None


# =============================================================================
# Enhancement #7: Amenities Taxonomy
# =============================================================================

class AmenityCategoryBase(BaseModel):
    """Amenity category base fields."""
    code: str
    name: str
    description: str | None = None
    icon: str | None = None
    display_order: int | None = 0
    lifestyle_weight: float | None = Field(None, ge=0, le=10)


class AmenityCategoryResponse(AmenityCategoryBase):
    """Amenity category API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int


class AmenityBase(BaseModel):
    """Amenity base fields."""
    code: str
    name: str
    description: str | None = None
    icon: str | None = None
    lifestyle_points: int | None = None


class AmenityResponse(AmenityBase):
    """Amenity API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    category_id: int


class AmenityTypeBase(BaseModel):
    """Amenity type/variant base fields."""
    variant_code: str
    variant_name: str
    description: str | None = None
    premium_multiplier: float | None = 1.0


class AmenityTypeResponse(AmenityTypeBase):
    """Amenity type API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    amenity_id: int


class ProjectAmenityResponse(BaseModel):
    """Project amenity linkage response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    amenity_type_id: int
    is_available: bool = True
    is_chargeable: bool | None = None
    monthly_fee: float | None = None
    quantity: int | None = 1
    size_sqft: float | None = None
    details: str | None = None
    images: list[str] | None = None


class AmenityTaxonomyFlat(BaseModel):
    """Flattened amenity for display (category > amenity > type)."""
    category_code: str
    category_name: str
    amenity_code: str
    amenity_name: str
    type_code: str
    type_name: str
    lifestyle_points: int | None = None
    premium_multiplier: float | None = 1.0


# =============================================================================
# Enhancement #8: Enhanced Unit Types
# =============================================================================

class EnhancedUnitTypeBase(BaseModel):
    """Enhanced unit type with all fields."""
    unit_label: str | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    balcony_count: int | None = None  # Enhancement #8
    
    # Enhancement #3: Normalized areas
    carpet_area_min_sqft: float | None = None
    carpet_area_max_sqft: float | None = None
    builtup_area_min_sqft: float | None = None
    builtup_area_max_sqft: float | None = None
    super_builtup_area_min_sqft: float | None = None
    super_builtup_area_max_sqft: float | None = None
    canonical_area_unit: AreaUnitEnum = AreaUnitEnum.SQFT
    
    # Enhancement #8: Maintenance
    maintenance_fee_monthly: float | None = None
    maintenance_fee_per_sqft: float | None = None


class EnhancedUnitTypeResponse(EnhancedUnitTypeBase):
    """Enhanced unit type API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    is_active: bool = True
    created_at: datetime | None = None


# =============================================================================
# Enhancement #9: Transaction Registry
# =============================================================================

class TransactionBase(BaseModel):
    """Transaction base fields."""
    registry_date: date | None = None
    registry_number: str | None = None
    sub_registrar_office: str | None = None
    
    # Amounts
    declared_amount: float | None = Field(None, description="Amount declared in registry")
    stamp_duty_paid: float | None = None
    registration_fee: float | None = None
    
    # Area
    registered_area_sqft: float | None = None
    area_type: str | None = Field(None, description="carpet, builtup, or super_builtup")
    price_per_sqft_registered: float | None = None
    
    # Buyer (anonymized)
    buyer_type: str | None = Field(None, description="individual, company, huf, nri")


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""
    project_id: int
    building_id: int | None = None
    unit_id: int | None = None
    anonymized_buyer_hash: str | None = None
    source_type: str | None = None
    source_reference: str | None = None


class TransactionResponse(TransactionBase):
    """Transaction API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    building_id: int | None = None
    unit_id: int | None = None
    created_at: datetime | None = None
    verified_at: datetime | None = None
    verification_status: str | None = None


class TransactionSummary(BaseModel):
    """Lightweight transaction for aggregations."""
    registry_date: date | None = None
    declared_amount: float | None = None
    registered_area_sqft: float | None = None
    price_per_sqft_registered: float | None = None


# =============================================================================
# Enhancement #10: Granular Ratings
# =============================================================================

class StructuredRatings(BaseModel):
    """Comprehensive structured ratings breakdown."""
    # Existing scores (normalized to 0-10 for consistency)
    connectivity: float | None = Field(None, ge=0, le=10)
    daily_needs: float | None = Field(None, ge=0, le=10)
    social_infra: float | None = Field(None, ge=0, le=10)
    
    # Enhancement #7: Lifestyle from amenity taxonomy
    lifestyle: float | None = Field(None, ge=0, le=10)
    
    # Enhancement #10: New ratings
    safety: float | None = Field(None, ge=0, le=10, description="Gated, CCTV, guards, etc.")
    environment: float | None = Field(None, ge=0, le=10, description="Green cover, air quality, noise")
    investment_potential: float | None = Field(None, ge=0, le=10, description="Price trends, appreciation")
    
    # Value for money (existing)
    value: float | None = Field(None, ge=0, le=10)


class EnhancedScoresResponse(BaseModel):
    """Enhanced scores with all ratings."""
    model_config = ConfigDict(from_attributes=True)
    
    # Existing scores (0-100 scale)
    overall_score: float | None = None
    amenity_score: float | None = None
    location_score: float | None = None
    value_score: float | None = None
    
    # Sub-scores
    connectivity_score: int | None = None
    daily_needs_score: int | None = None
    social_infra_score: int | None = None
    
    # Enhancement #7 & #10
    lifestyle_score: float | None = None
    safety_score: float | None = None
    environment_score: float | None = None
    investment_potential_score: float | None = None
    
    # Full structured breakdown
    structured_ratings: StructuredRatings | None = None
    
    # Metadata
    score_status: str | None = None
    score_status_reason: dict[str, Any] | list[str] | str | None = None
    score_version: str | None = None
    last_computed_at: datetime | None = None


# =============================================================================
# Composite Response Types
# =============================================================================

class EnhancedProjectDetail(BaseModel):
    """
    Full project detail with all enhancements.
    Used for detailed project view.
    """
    # Core info
    project_id: int
    name: str
    rera_number: str | None = None
    status: str | None = None
    
    # Enhancement #1: Developer
    developer: DeveloperSummary | None = None
    
    # Enhancement #5: Possession
    possession_timeline: PossessionTimelineResponse | None = None
    
    # Location
    location: dict[str, Any] | None = None
    
    # Enhancement #10: Scores
    scores: EnhancedScoresResponse | None = None
    
    # Enhancement #4: Pricing
    pricing: PricingByAreaType | None = None
    
    # Enhancement #8: Unit types
    unit_types: list[EnhancedUnitTypeResponse] = Field(default_factory=list)
    
    # Enhancement #7: Amenities with taxonomy
    amenities: list[ProjectAmenityResponse] = Field(default_factory=list)
    amenities_flat: list[AmenityTaxonomyFlat] = Field(default_factory=list)
    
    # Enhancement #2: Units summary
    units_summary: dict[str, Any] | None = Field(
        default=None,
        description="Summary: total_units, available, sold, by_status, by_floor"
    )
    
    # Enhancement #9: Transaction stats
    transaction_stats: dict[str, Any] | None = Field(
        default=None,
        description="Stats: total_transactions, avg_price_per_sqft, price_trend"
    )


class ProjectHierarchy(BaseModel):
    """
    Full project hierarchy: Project > Towers > Units.
    Enhancement #2: Hierarchy Restructuring
    """
    project_id: int
    project_name: str
    towers: list["TowerWithUnits"] = Field(default_factory=list)


class TowerWithUnits(BaseModel):
    """Tower/Building with its units."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    building_name: str
    building_type: str | None = None
    number_of_floors: int | None = None
    total_units: int | None = None
    status: str | None = None
    units: list[UnitSummary] = Field(default_factory=list)


# Resolve forward references
ProjectHierarchy.model_rebuild()


__all__ = [
    # Enums
    "AreaUnitEnum",
    "ProjectPhaseEnum",
    "UnitStatusEnum",
    "AmenityCategoryEnum",
    
    # Enhancement #1
    "DeveloperBase",
    "DeveloperCreate",
    "DeveloperResponse",
    "DeveloperSummary",
    
    # Enhancement #2
    "UnitBase",
    "UnitCreate",
    "UnitResponse",
    "UnitSummary",
    
    # Enhancement #3
    "NormalizedArea",
    
    # Enhancement #4
    "PricingByAreaType",
    
    # Enhancement #5
    "PossessionTimelineBase",
    "PossessionTimelineCreate",
    "PossessionTimelineResponse",
    
    # Enhancement #7
    "AmenityCategoryBase",
    "AmenityCategoryResponse",
    "AmenityBase",
    "AmenityResponse",
    "AmenityTypeBase",
    "AmenityTypeResponse",
    "ProjectAmenityResponse",
    "AmenityTaxonomyFlat",
    
    # Enhancement #8
    "EnhancedUnitTypeBase",
    "EnhancedUnitTypeResponse",
    
    # Enhancement #9
    "TransactionBase",
    "TransactionCreate",
    "TransactionResponse",
    "TransactionSummary",
    
    # Enhancement #10
    "StructuredRatings",
    "EnhancedScoresResponse",
    
    # Composite
    "EnhancedProjectDetail",
    "ProjectHierarchy",
    "TowerWithUnits",
]
