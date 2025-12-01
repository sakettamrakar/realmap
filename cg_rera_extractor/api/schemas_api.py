"""
API Schemas for Points 11-17: 7-Point API Standard.

This module defines DTOs for:
- Unified Project Identity (Point 11)
- Rich Media (Point 12)
- Price Trends Analytics (Point 13)
- Gated Brochure Access (Point 14)
- JSON-LD SEO (Point 15)
- API Discovery & Metadata (Point 16)
- Data Provenance (Point 17)
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# =============================================================================
# Generic Response Envelope (Point 16)
# =============================================================================

T = TypeVar("T")


class PaginationLinks(BaseModel):
    """HATEOAS pagination links."""
    self_link: str = Field(..., alias="self")
    next_link: str | None = Field(None, alias="next")
    prev_link: str | None = Field(None, alias="prev")
    first_link: str = Field(..., alias="first")
    last_link: str | None = Field(None, alias="last")
    
    model_config = ConfigDict(populate_by_name=True)


class ResponseMeta(BaseModel):
    """Standard response metadata envelope."""
    api_version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str | None = None
    
    # Pagination fields (optional - for list endpoints)
    limit: int | None = None
    offset: int | None = None
    total_count: int | None = None
    page: int | None = None
    page_size: int | None = None
    total_pages: int | None = None


class EnvelopedResponse(BaseModel, Generic[T]):
    """
    Standard response wrapper with metadata and HATEOAS links.
    
    All API responses should use this envelope for consistency.
    """
    data: T
    meta: ResponseMeta
    links: PaginationLinks | None = None


class EnvelopedListResponse(BaseModel, Generic[T]):
    """Response wrapper for paginated list endpoints."""
    data: list[T]
    meta: ResponseMeta
    links: PaginationLinks


# =============================================================================
# Data Provenance (Point 17)
# =============================================================================

class ExtractionMethodEnum(str, Enum):
    """How the data was collected."""
    SCRAPER = "scraper"
    MANUAL = "manual"
    FEED = "feed"
    API = "api"
    OCR = "ocr"


class DataProvenance(BaseModel):
    """
    Trust layer metadata for every record.
    
    Exposes extraction metadata so consumers know where data came from.
    """
    last_updated_at: datetime | None = None
    source_domain: str | None = Field(None, description="e.g., 'rera.cg.gov.in'")
    extraction_method: ExtractionMethodEnum | None = None
    confidence_score: float | None = Field(None, ge=0, le=1, description="0-1.0 confidence")
    data_quality_score: int | None = Field(None, ge=0, le=100, description="0-100 quality")
    raw_source_url: str | None = None
    last_verified_at: datetime | None = None


# =============================================================================
# Unified Project Identity (Point 11)
# =============================================================================

class UnitSummary(BaseModel):
    """Individual unit in the hierarchy."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    floor_number: int | None = None
    unit_number: str | None = None
    status: str | None = None
    carpet_area_sqft: float | None = None
    builtup_area_sqft: float | None = None
    super_builtup_area_sqft: float | None = None
    price_total: float | None = None


class TowerHierarchy(BaseModel):
    """Building/Tower with nested units."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    building_name: str
    building_type: str | None = None
    number_of_floors: int | None = None
    total_units: int | None = None
    status: str | None = None
    units: list[UnitSummary] = Field(default_factory=list)


class ProjectHierarchy(BaseModel):
    """
    Full hierarchical tree: Project → Tower → Unit.
    
    Optimized for SSR with all relationships loaded in a single query.
    """
    model_config = ConfigDict(from_attributes=True)
    
    # Core identity
    id: int
    rera_id: str = Field(..., description="RERA registration number")
    state_code: str
    name: str
    
    # Status & dates
    status: str | None = None
    registration_date: date | None = None
    expected_completion: date | None = None
    
    # Location
    district: str | None = None
    tehsil: str | None = None
    address: str | None = None
    lat: float | None = None
    lon: float | None = None
    
    # Developer
    developer_id: int | None = None
    developer_name: str | None = None
    
    # Hierarchy (Tower → Unit tree)
    towers: list[TowerHierarchy] = Field(default_factory=list)
    
    # Unit type summary (aggregate)
    unit_types: list[dict[str, Any]] = Field(default_factory=list)
    
    # Provenance
    provenance: DataProvenance | None = None


# =============================================================================
# Rich Media & Asset Management (Point 12)
# =============================================================================

class MediaTypeEnum(str, Enum):
    """Type of media asset."""
    GALLERY = "gallery"
    FLOORPLAN = "floorplan"
    MASTERPLAN = "masterplan"
    BROCHURE = "brochure"
    VIDEO = "video"
    VIRTUAL_TOUR = "virtual_tour"
    ELEVATION = "elevation"
    AMENITY = "amenity"


class LicenseTypeEnum(str, Enum):
    """License type for media assets."""
    PROPRIETARY = "proprietary"
    PUBLIC_DOMAIN = "public_domain"
    CREATIVE_COMMONS = "creative_commons"
    RERA_OFFICIAL = "rera_official"


class MediaAsset(BaseModel):
    """
    Rich media asset with full metadata.
    
    Never returns just URL strings - always structured objects.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    type: MediaTypeEnum
    url: str
    thumbnail_url: str | None = None
    
    # Dimensions (for images)
    width_px: int | None = None
    height_px: int | None = None
    
    # File metadata
    filesize_kb: int | None = None
    file_format: str | None = Field(None, description="jpg, png, pdf, mp4")
    mime_type: str | None = None
    
    # Licensing
    license_type: LicenseTypeEnum = LicenseTypeEnum.PROPRIETARY
    attribution: str | None = None
    
    # Relationships
    unit_type_id: int | None = Field(None, description="For floorplans linked to unit types")
    unit_type_label: str | None = None
    
    # Metadata
    title: str | None = None
    description: str | None = None
    sort_order: int = 0
    is_primary: bool = False
    
    # Provenance
    source_url: str | None = None
    captured_at: datetime | None = None


class ProjectMediaResponse(BaseModel):
    """Response for GET /projects/{id}/media."""
    project_id: int
    project_name: str
    
    gallery: list[MediaAsset] = Field(default_factory=list)
    floorplans: list[MediaAsset] = Field(default_factory=list)
    masterplans: list[MediaAsset] = Field(default_factory=list)
    brochures: list[MediaAsset] = Field(default_factory=list)
    videos: list[MediaAsset] = Field(default_factory=list)
    
    total_count: int = 0


# =============================================================================
# Price Trends & Analytics (Point 13)
# =============================================================================

class TimeframeEnum(str, Enum):
    """Analysis timeframe."""
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"
    TWO_YEARS = "2Y"
    FIVE_YEARS = "5Y"
    ALL = "ALL"


class GranularityEnum(str, Enum):
    """Time-series granularity."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class EntityTypeEnum(str, Enum):
    """Type of entity for analytics."""
    PROJECT = "project"
    LOCALITY = "locality"
    DISTRICT = "district"
    DEVELOPER = "developer"


class PriceTrendDataPoint(BaseModel):
    """Single data point in a price trend time-series."""
    period: str = Field(..., description="e.g., 'Q1-2024', '2024-03', 'Mar 2024'")
    period_start: date
    period_end: date
    
    # Price metrics
    avg_price_per_sqft: float | None = None
    min_price_per_sqft: float | None = None
    max_price_per_sqft: float | None = None
    median_price_per_sqft: float | None = None
    
    avg_total_price: float | None = None
    min_total_price: float | None = None
    max_total_price: float | None = None
    
    # Volume & change
    transaction_volume: int | None = Field(None, description="Number of transactions")
    inventory_count: int | None = Field(None, description="Available units")
    
    # Change metrics
    change_pct: float | None = Field(None, description="% change from previous period")
    change_abs: float | None = Field(None, description="Absolute change from previous period")
    
    # Confidence
    sample_size: int | None = None
    confidence_level: str | None = Field(None, description="high/medium/low")


class PriceTrendRequest(BaseModel):
    """Request parameters for price trends."""
    entity_id: int = Field(..., description="Project, Locality, or District ID")
    entity_type: EntityTypeEnum = EntityTypeEnum.PROJECT
    timeframe: TimeframeEnum = TimeframeEnum.ONE_YEAR
    granularity: GranularityEnum = GranularityEnum.QUARTERLY
    
    # Optional filters
    unit_type: str | None = Field(None, description="Filter by unit type e.g., '2BHK'")
    area_type: str | None = Field(None, description="carpet, builtup, super_builtup")


class PriceTrendResponse(BaseModel):
    """Response for GET /analytics/price-trends."""
    entity_id: int
    entity_type: EntityTypeEnum
    entity_name: str
    
    timeframe: TimeframeEnum
    granularity: GranularityEnum
    
    # Time-series data
    trend_data: list[PriceTrendDataPoint]
    
    # Summary statistics
    current_avg_price: float | None = None
    period_high: float | None = None
    period_low: float | None = None
    overall_change_pct: float | None = None
    
    # Metadata
    data_points_count: int = 0
    earliest_date: date | None = None
    latest_date: date | None = None
    
    # Provenance
    provenance: DataProvenance | None = None


class LocalityTrendComparison(BaseModel):
    """Compare trends across multiple localities."""
    localities: list[PriceTrendResponse]
    benchmark_locality: str | None = None


# =============================================================================
# Gated Brochure Access (Point 14) - Security
# =============================================================================

class BrochureAccessRequest(BaseModel):
    """
    Lead capture request for brochure access.
    
    User must provide consent and contact details before receiving the download link.
    """
    project_id: int
    document_id: int | None = Field(None, description="Specific document, or latest brochure")
    
    # Lead capture (at least one required)
    email: str | None = None
    phone: str | None = None
    name: str | None = None
    
    # Consent
    marketing_consent: bool = Field(False, description="Consent for marketing communications")
    privacy_consent: bool = Field(True, description="Consent to privacy policy")
    
    # Optional context
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    referrer_url: str | None = None


class SignedUrlResponse(BaseModel):
    """
    Time-limited signed URL for secure document access.
    
    The URL expires after 15 minutes and cannot be shared.
    """
    download_url: str = Field(..., description="Presigned URL for download")
    expires_at: datetime
    expires_in_seconds: int = Field(900, description="Seconds until expiry (default 15 min)")
    
    # Document metadata
    document_id: int
    filename: str
    file_format: str
    filesize_kb: int | None = None
    
    # Access tracking
    access_token: str = Field(..., description="Token for tracking/analytics")
    download_limit: int = Field(3, description="Max downloads per token")


class BrochureAccessResponse(BaseModel):
    """Response for POST /access/brochure."""
    success: bool
    signed_url: SignedUrlResponse | None = None
    
    # Lead tracking
    lead_id: str | None = Field(None, description="CRM lead identifier")
    
    # Error handling
    error_code: str | None = None
    error_message: str | None = None


# =============================================================================
# JSON-LD SEO (Point 15)
# =============================================================================

class SchemaOrgOffer(BaseModel):
    """Schema.org Offer for pricing."""
    type: str = Field("Offer", alias="@type")
    price_currency: str = Field("INR", alias="priceCurrency")
    price: float | None = None
    price_range: str | None = Field(None, alias="priceRange", description="e.g., '₹50L - ₹1.2Cr'")
    availability: str | None = None  # https://schema.org/InStock
    valid_from: str | None = Field(None, alias="validFrom")
    
    model_config = ConfigDict(populate_by_name=True)


class SchemaOrgAggregateRating(BaseModel):
    """Schema.org AggregateRating."""
    type: str = Field("AggregateRating", alias="@type")
    rating_value: float = Field(..., alias="ratingValue", ge=0, le=5)
    best_rating: int = Field(5, alias="bestRating")
    worst_rating: int = Field(1, alias="worstRating")
    rating_count: int | None = Field(None, alias="ratingCount")
    review_count: int | None = Field(None, alias="reviewCount")
    
    model_config = ConfigDict(populate_by_name=True)


class SchemaOrgGeoCoordinates(BaseModel):
    """Schema.org GeoCoordinates."""
    type: str = Field("GeoCoordinates", alias="@type")
    latitude: float
    longitude: float
    
    model_config = ConfigDict(populate_by_name=True)


class SchemaOrgAddress(BaseModel):
    """Schema.org PostalAddress."""
    type: str = Field("PostalAddress", alias="@type")
    street_address: str | None = Field(None, alias="streetAddress")
    address_locality: str | None = Field(None, alias="addressLocality")
    address_region: str | None = Field(None, alias="addressRegion")
    postal_code: str | None = Field(None, alias="postalCode")
    address_country: str = Field("IN", alias="addressCountry")
    
    model_config = ConfigDict(populate_by_name=True)


class SchemaOrgOrganization(BaseModel):
    """Schema.org Organization (for developer)."""
    type: str = Field("Organization", alias="@type")
    name: str
    url: str | None = None
    logo: str | None = None
    
    model_config = ConfigDict(populate_by_name=True)


class SchemaOrgProduct(BaseModel):
    """
    Schema.org Product/Residence structured data.
    
    This is injected into API responses for SEO purposes.
    Google uses this for rich search results.
    """
    context: str = Field("https://schema.org", alias="@context")
    type: str = Field("Product", alias="@type")  # or "Residence" for real estate
    
    # Identity
    name: str
    description: str | None = None
    sku: str | None = Field(None, description="RERA registration number")
    product_id: str | None = Field(None, alias="productID")
    
    # Media
    image: list[str] | None = None
    url: str | None = None
    
    # Location
    geo: SchemaOrgGeoCoordinates | None = None
    address: SchemaOrgAddress | None = None
    
    # Provider (Developer)
    brand: SchemaOrgOrganization | None = None
    manufacturer: SchemaOrgOrganization | None = None
    
    # Pricing
    offers: SchemaOrgOffer | None = None
    
    # Rating
    aggregate_rating: SchemaOrgAggregateRating | None = Field(None, alias="aggregateRating")
    
    # Additional properties
    additional_property: list[dict[str, Any]] | None = Field(None, alias="additionalProperty")
    
    model_config = ConfigDict(populate_by_name=True)


class JsonLdWrapper(BaseModel):
    """
    Container for JSON-LD data.
    
    Included in API responses as `schema_org` field.
    """
    schema_org: SchemaOrgProduct
    
    # Additional structured data types if needed
    breadcrumb: dict[str, Any] | None = None
    faq: dict[str, Any] | None = None


# =============================================================================
# API Discovery (Point 16)
# =============================================================================

class ResourceEndpoint(BaseModel):
    """Description of an API resource."""
    name: str
    path: str
    methods: list[str]
    description: str | None = None
    requires_auth: bool = False
    deprecated: bool = False
    version: str = "1.0"


class ApiMetaResponse(BaseModel):
    """
    Response for GET /api/meta.
    
    Lists all available resources for API discovery/crawlers.
    """
    api_name: str = "CG RERA Projects API"
    api_version: str = "1.0.0"
    base_url: str
    documentation_url: str | None = None
    
    # Available resources
    resources: list[ResourceEndpoint]
    
    # Rate limits
    rate_limit: int | None = Field(None, description="Requests per minute")
    
    # Health
    status: str = "healthy"
    uptime_seconds: int | None = None


# =============================================================================
# Enhanced Project Detail (Combines all enhancements)
# =============================================================================

class ProjectDetailV3(BaseModel):
    """
    Enhanced project detail combining all Points 11-17.
    
    This is the next-generation project detail response.
    """
    # Core data
    project: ProjectHierarchy
    
    # Location
    location: dict[str, Any]
    
    # Scores & ratings
    scores: dict[str, Any]
    
    # Amenities
    amenities: dict[str, Any]
    
    # Pricing
    pricing: dict[str, Any] | None = None
    
    # QA status
    qa: dict[str, Any]
    
    # Score explanation
    score_explanation: dict[str, Any] | None = None
    
    # NEW: SEO structured data (Point 15)
    schema_org: SchemaOrgProduct | None = None
    
    # NEW: Data provenance (Point 17)
    provenance: DataProvenance | None = None
    
    # NEW: Media (Point 12 - summary)
    media_summary: dict[str, int] | None = Field(
        None, description="Count of each media type"
    )


# =============================================================================
# Export all schemas
# =============================================================================

__all__ = [
    # Envelope (Point 16)
    "PaginationLinks",
    "ResponseMeta",
    "EnvelopedResponse",
    "EnvelopedListResponse",
    
    # Provenance (Point 17)
    "ExtractionMethodEnum",
    "DataProvenance",
    
    # Unified Identity (Point 11)
    "UnitSummary",
    "TowerHierarchy",
    "ProjectHierarchy",
    
    # Rich Media (Point 12)
    "MediaTypeEnum",
    "LicenseTypeEnum",
    "MediaAsset",
    "ProjectMediaResponse",
    
    # Price Trends (Point 13)
    "TimeframeEnum",
    "GranularityEnum",
    "EntityTypeEnum",
    "PriceTrendDataPoint",
    "PriceTrendRequest",
    "PriceTrendResponse",
    "LocalityTrendComparison",
    
    # Gated Brochure (Point 14)
    "BrochureAccessRequest",
    "SignedUrlResponse",
    "BrochureAccessResponse",
    
    # JSON-LD (Point 15)
    "SchemaOrgOffer",
    "SchemaOrgAggregateRating",
    "SchemaOrgGeoCoordinates",
    "SchemaOrgAddress",
    "SchemaOrgOrganization",
    "SchemaOrgProduct",
    "JsonLdWrapper",
    
    # API Discovery (Point 16)
    "ResourceEndpoint",
    "ApiMetaResponse",
    
    # Enhanced Detail
    "ProjectDetailV3",
]
