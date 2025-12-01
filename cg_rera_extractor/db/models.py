"""SQLAlchemy ORM models for CG RERA projects."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class Project(Base):
    """Primary project record keyed by state and registration number."""

    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint(
            "state_code", "rera_registration_number", name="uq_projects_state_reg_number"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_code: Mapped[str] = mapped_column(String(10), nullable=False)
    rera_registration_number: Mapped[str] = mapped_column(String(100), nullable=False)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(128))
    tehsil: Mapped[str | None] = mapped_column(String(128))
    village_or_locality: Mapped[str | None] = mapped_column(String(255))
    full_address: Mapped[str | None] = mapped_column(String(512))
    normalized_address: Mapped[str | None] = mapped_column(String(512))
    pincode: Mapped[str | None] = mapped_column(String(20))
    latitude: Mapped[Numeric | None] = mapped_column(
        Numeric(9, 6), doc="Latitude in decimal degrees"
    )
    longitude: Mapped[Numeric | None] = mapped_column(
        Numeric(9, 6), doc="Longitude in decimal degrees"
    )
    geocoding_status: Mapped[str | None] = mapped_column(
        String(64), doc="Lifecycle flag for geocoding runs"
    )
    geocoding_source: Mapped[str | None] = mapped_column(
        String(64), doc="Legacy source label for geocoding"
    )
    geo_source: Mapped[str | None] = mapped_column(
        String(128), doc="Canonical source/provider for GEO data"
    )
    geo_precision: Mapped[str | None] = mapped_column(
        String(32), doc="Precision level such as ROOFTOP/LOCALITY/CITY_CENTROID"
    )
    geo_confidence: Mapped[Numeric | None] = mapped_column(
        Numeric(4, 3), doc="Optional confidence score from the geocoder"
    )
    geo_normalized_address: Mapped[str | None] = mapped_column(
        String(512), doc="Normalized address string used for geocoding"
    )
    geo_formatted_address: Mapped[str | None] = mapped_column(
        String(512), doc="Formatted address returned by the geocoder"
    )
    approved_date: Mapped[date | None] = mapped_column(Date())
    proposed_end_date: Mapped[date | None] = mapped_column(Date())
    extended_end_date: Mapped[date | None] = mapped_column(Date())
    raw_data_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    scraped_at: Mapped[date | None] = mapped_column(DateTime(timezone=True))
    data_quality_score: Mapped[int | None] = mapped_column(Integer)
    last_parsed_at: Mapped[date | None] = mapped_column(DateTime(timezone=True))
    
    # ==========================================================================
    # POINT 27: Automated QA Gates & Price Sanity Checks
    # ==========================================================================
    qa_flags: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        doc="QA validation flags: {price_outlier, missing_critical, bounds_exceeded, locality_mismatch}"
    )
    qa_status: Mapped[str | None] = mapped_column(
        String(32),
        doc="Overall QA status: passed, warning, failed, pending"
    )
    qa_last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        doc="Timestamp of last QA validation"
    )

    promoters: Mapped[list["Promoter"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    buildings: Mapped[list["Building"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    unit_types: Mapped[list["UnitType"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    documents: Mapped[list["ProjectDocument"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    quarterly_updates: Mapped[list["QuarterlyUpdate"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    bank_accounts: Mapped[list["BankAccount"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    land_parcels: Mapped[list["LandParcel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    artifacts: Mapped[list["ProjectArtifact"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    amenity_stats: Mapped[list["ProjectAmenityStats"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    score: Mapped["ProjectScores"] = relationship(
        back_populates="project", cascade="all, delete-orphan", uselist=False
    )
    locations: Mapped[list["ProjectLocation"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    project_unit_types: Mapped[list["ProjectUnitType"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    pricing_snapshots: Mapped[list["ProjectPricingSnapshot"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    provenance_records: Mapped[list["DataProvenance"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Promoter(Base):
    """Details for the project's promoter/owner."""

    __tablename__ = "promoters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    promoter_name: Mapped[str] = mapped_column(String(255), nullable=False)
    promoter_type: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(String(512))
    website: Mapped[str | None] = mapped_column(String(255))

    project: Mapped[Project] = relationship(back_populates="promoters")


class Building(Base):
    """Represents a building/tower/block within a project."""

    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    building_name: Mapped[str] = mapped_column(String(255), nullable=False)
    building_type: Mapped[str | None] = mapped_column(String(100))
    number_of_floors: Mapped[int | None] = mapped_column(Integer)
    total_units: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str | None] = mapped_column(String(100))

    project: Mapped[Project] = relationship(back_populates="buildings")


class UnitType(Base):
    """Unit type mix for a project (1BHK/2BHK/etc.)."""

    __tablename__ = "unit_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    carpet_area_sqmt: Mapped[Numeric | None] = mapped_column(Numeric(12, 2))
    saleable_area_sqmt: Mapped[Numeric | None] = mapped_column(Numeric(12, 2))
    total_units: Mapped[int | None] = mapped_column(Integer)
    sale_price: Mapped[Numeric | None] = mapped_column(Numeric(14, 2))

    project: Mapped[Project] = relationship(back_populates="unit_types")


class ProjectDocument(Base):
    """Documents uploaded for the project (approvals, certificates, etc.)."""

    __tablename__ = "project_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    doc_type: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(1024))

    project: Mapped[Project] = relationship(back_populates="documents")


class QuarterlyUpdate(Base):
    """Quarterly progress update for a project."""

    __tablename__ = "quarterly_updates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    quarter: Mapped[str | None] = mapped_column(String(32))
    update_date: Mapped[date | None] = mapped_column(Date())
    status: Mapped[str | None] = mapped_column(String(100))
    summary: Mapped[str | None] = mapped_column(String(512))
    raw_data_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    project: Mapped[Project] = relationship(back_populates="quarterly_updates")


class BankAccount(Base):
    """RERA designated bank account for the project."""

    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    bank_name: Mapped[str | None] = mapped_column(String(255))
    branch_name: Mapped[str | None] = mapped_column(String(255))
    account_number: Mapped[str | None] = mapped_column(String(100))
    ifsc_code: Mapped[str | None] = mapped_column(String(20))
    account_holder_name: Mapped[str | None] = mapped_column(String(255))

    project: Mapped[Project] = relationship(back_populates="bank_accounts")


class LandParcel(Base):
    """Details about the land parcel."""

    __tablename__ = "land_parcels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    survey_number: Mapped[str | None] = mapped_column(String(255))
    area_sqmt: Mapped[Numeric | None] = mapped_column(Numeric(12, 2))
    owner_name: Mapped[str | None] = mapped_column(String(255))
    encumbrance_details: Mapped[str | None] = mapped_column(String(1024))

    project: Mapped[Project] = relationship(back_populates="land_parcels")


class ProjectArtifact(Base):
    """Any file associated with the project (Documents, Images, Plans)."""

    __tablename__ = "project_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50))  # legal, technical, etc.
    artifact_type: Mapped[str | None] = mapped_column(String(100))  # reg_cert, building_plan
    file_path: Mapped[str | None] = mapped_column(String(1024))  # Relative path
    source_url: Mapped[str | None] = mapped_column(String(1024))  # Original URL
    file_format: Mapped[str | None] = mapped_column(String(20))  # pdf, jpg
    is_preview: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped[Project] = relationship(back_populates="artifacts")


class AmenityPOI(Base):
    """Cached amenity point of interest from a provider."""

    __tablename__ = "amenity_poi"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_place_id",
            name="uq_amenity_poi_provider_place_id",
        ),
        Index("ix_amenity_poi_type_lat_lon", "amenity_type", "lat", "lon"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_place_id: Mapped[str] = mapped_column(String(255), nullable=False)
    amenity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    lat: Mapped[Numeric] = mapped_column(Numeric(9, 6), nullable=False)
    lon: Mapped[Numeric] = mapped_column(Numeric(9, 6), nullable=False)
    formatted_address: Mapped[str | None] = mapped_column(String(1024))
    source_raw: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    last_seen_at: Mapped[date | None] = mapped_column(DateTime(timezone=True))
    search_radius_km: Mapped[Numeric | None] = mapped_column(Numeric(4, 2))
    created_at: Mapped[date | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[date | None] = mapped_column(DateTime(timezone=True))

    def touch_last_seen(self) -> None:
        now = datetime.now(timezone.utc)
        self.last_seen_at = now
        self.updated_at = now


class ProjectAmenityStats(Base):
    """Aggregated amenity statistics per project, amenity type, and radius."""

    __tablename__ = "project_amenity_stats"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "amenity_type",
            "radius_km",
            name="uq_project_amenity_slice",
        ),
        Index("ix_project_amenity_stats_project_id", "project_id"),
        Index("ix_project_amenity_stats_amenity_type", "amenity_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    amenity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # Nearby / Location Context
    radius_km: Mapped[Numeric | None] = mapped_column(Numeric(4, 2)) # Nullable for onsite
    nearby_count: Mapped[int | None] = mapped_column(Integer)
    nearby_nearest_km: Mapped[Numeric | None] = mapped_column(Numeric(6, 3))
    
    # Onsite / Project Amenities
    onsite_available: Mapped[bool | None] = mapped_column(Boolean)
    onsite_details: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    
    provider_snapshot: Mapped[str | None] = mapped_column(String(128))
    last_computed_at: Mapped[date | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project] = relationship(back_populates="amenity_stats")


class ProjectScores(Base):
    """Composite amenity-based scores per project."""

    __tablename__ = "project_scores"
    __table_args__ = (
        UniqueConstraint("project_id", name="uq_project_scores_project_id"),
        Index("ix_project_scores_project_id", "project_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    amenity_score: Mapped[Numeric | None] = mapped_column(Numeric(5, 2))
    location_score: Mapped[Numeric | None] = mapped_column(Numeric(5, 2))
    
    # Location sub-scores
    connectivity_score: Mapped[int | None] = mapped_column(Integer)
    daily_needs_score: Mapped[int | None] = mapped_column(Integer)
    social_infra_score: Mapped[int | None] = mapped_column(Integer)
    
    overall_score: Mapped[Numeric | None] = mapped_column(Numeric(5, 2))
    score_status: Mapped[str | None] = mapped_column(String(32))
    score_status_reason: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    
    # Value-for-money score combining quality and price
    value_score: Mapped[Numeric | None] = mapped_column(Numeric(5, 2))
    
    # Enhancement #7: Lifestyle score from amenity taxonomy
    lifestyle_score: Mapped[Numeric | None] = mapped_column(
        Numeric(4, 2), doc="0-10 score based on amenity taxonomy weights"
    )
    
    # Enhancement #10: Granular Ratings System
    safety_score: Mapped[Numeric | None] = mapped_column(
        Numeric(4, 2), doc="0-10 safety rating (gated, CCTV, guards, etc.)"
    )
    environment_score: Mapped[Numeric | None] = mapped_column(
        Numeric(4, 2), doc="0-10 environment rating (green cover, air quality, noise)"
    )
    investment_potential_score: Mapped[Numeric | None] = mapped_column(
        Numeric(4, 2), doc="0-10 investment potential (price trends, appreciation)"
    )
    
    # Structured ratings JSON for extensibility
    structured_ratings: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, doc="Full breakdown: {connectivity, lifestyle, safety, environment, investment_potential}"
    )
    
    score_version: Mapped[str | None] = mapped_column(String(32))
    last_computed_at: Mapped[date | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project] = relationship(back_populates="score")


class ProjectLocation(Base):
    """Candidate location for a project from a specific source."""

    __tablename__ = "project_locations"
    __table_args__ = (
        Index("ix_project_locations_project_id", "project_id"),
        Index("ix_project_locations_source_type", "source_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    lat: Mapped[Numeric] = mapped_column(Numeric(9, 6), nullable=False)
    lon: Mapped[Numeric] = mapped_column(Numeric(9, 6), nullable=False)
    precision_level: Mapped[str | None] = mapped_column(String(32))
    confidence_score: Mapped[Numeric | None] = mapped_column(Numeric(4, 3))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    meta_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="locations")


class ProjectUnitType(Base):
    """Canonical unit configuration within a project."""

    __tablename__ = "project_unit_types"
    __table_args__ = (
        Index("ix_project_unit_types_project_id", "project_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    unit_label: Mapped[str | None] = mapped_column(String(100))
    bedrooms: Mapped[int | None] = mapped_column(Integer)
    bathrooms: Mapped[int | None] = mapped_column(Integer)
    # Enhancement #8: Add balcony_count
    balcony_count: Mapped[int | None] = mapped_column(Integer)
    
    # Enhancement #3: Explicit Area Normalization - all three area types
    carpet_area_min_sqft: Mapped[Numeric | None] = mapped_column(Numeric(10, 2))
    carpet_area_max_sqft: Mapped[Numeric | None] = mapped_column(Numeric(10, 2))
    builtup_area_min_sqft: Mapped[Numeric | None] = mapped_column(Numeric(10, 2))
    builtup_area_max_sqft: Mapped[Numeric | None] = mapped_column(Numeric(10, 2))
    super_builtup_area_min_sqft: Mapped[Numeric | None] = mapped_column(Numeric(10, 2))
    super_builtup_area_max_sqft: Mapped[Numeric | None] = mapped_column(Numeric(10, 2))
    # Enhancement #3: Canonical area unit
    canonical_area_unit: Mapped[str | None] = mapped_column(
        String(10), default="SQFT", doc="SQFT or SQM"
    )
    
    # Enhancement #8: Maintenance fee
    maintenance_fee_monthly: Mapped[Numeric | None] = mapped_column(
        Numeric(10, 2), doc="Monthly maintenance fee per unit"
    )
    maintenance_fee_per_sqft: Mapped[Numeric | None] = mapped_column(
        Numeric(8, 2), doc="Maintenance fee per sqft"
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="project_unit_types")


# =============================================================================
# POINT 29: Content Provenance (Audit Trail)
# =============================================================================


class DataProvenance(Base):
    """
    Audit trail for scraped data - tracks extraction source, method, and confidence.
    
    Point 29 Implementation: Content Provenance
    - snapshot_url: Original scraped URL
    - extraction_method: Parser version used (e.g., 'v1_json_parser_2.1')
    - confidence_score: Extraction confidence (0.0-1.0)
    - network_log_ref: Reference to HAR file for replay
    """

    __tablename__ = "data_provenance"
    __table_args__ = (
        Index("ix_data_provenance_project_id", "project_id"),
        Index("ix_data_provenance_scraped_at", "scraped_at"),
        Index("ix_data_provenance_extraction_method", "extraction_method"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    
    # Source tracking
    snapshot_url: Mapped[str | None] = mapped_column(
        String(2048), doc="Original URL that was scraped"
    )
    source_domain: Mapped[str | None] = mapped_column(
        String(255), doc="Domain of the source (e.g., 'rera.cg.gov.in')"
    )
    
    # Extraction metadata
    extraction_method: Mapped[str] = mapped_column(
        String(128), nullable=False, doc="Parser version (e.g., 'v1_json_parser_2.1')"
    )
    parser_version: Mapped[str | None] = mapped_column(
        String(64), doc="Specific parser version number"
    )
    confidence_score: Mapped[Numeric | None] = mapped_column(
        Numeric(4, 3), doc="Extraction confidence 0.000-1.000"
    )
    
    # Network trace reference (Point 28 integration)
    network_log_ref: Mapped[str | None] = mapped_column(
        String(1024), doc="Path to HAR file or network trace archive"
    )
    html_snapshot_path: Mapped[str | None] = mapped_column(
        String(1024), doc="Path to saved HTML snapshot"
    )
    
    # Run context
    run_id: Mapped[str | None] = mapped_column(
        String(128), doc="Scraper run identifier"
    )
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    
    # Validation at extraction time
    extraction_warnings: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, doc="Warnings/issues during extraction"
    )
    fields_extracted: Mapped[int | None] = mapped_column(
        Integer, doc="Count of fields successfully extracted"
    )
    fields_expected: Mapped[int | None] = mapped_column(
        Integer, doc="Count of fields expected from schema"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="provenance_records")


# =============================================================================
# POINT 28: Network Trace Replayability
# =============================================================================


class IngestionAudit(Base):
    """
    Full ingestion audit record with network trace references.
    
    Point 28 Implementation: Network Trace Replayability
    - Captures full HTTP context per scrape session
    - Links to HAR files for debugging failed extractions
    - Stores request/response metadata for replay capability
    """

    __tablename__ = "ingestion_audits"
    __table_args__ = (
        Index("ix_ingestion_audits_run_id", "run_id"),
        Index("ix_ingestion_audits_status", "status"),
        Index("ix_ingestion_audits_started_at", "started_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Run identification
    run_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    run_type: Mapped[str | None] = mapped_column(
        String(64), doc="Type: full_crawl, incremental, retry, manual"
    )
    
    # Configuration snapshot
    config_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, doc="Scraper config used for this run"
    )
    
    # Execution tracking
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="running",
        doc="running, completed, failed, partial"
    )
    
    # Network trace storage
    har_file_path: Mapped[str | None] = mapped_column(
        String(1024), doc="Path to HAR archive for this run"
    )
    network_log_size_bytes: Mapped[int | None] = mapped_column(
        Integer, doc="Size of network trace data"
    )
    
    # Statistics
    projects_attempted: Mapped[int | None] = mapped_column(Integer, default=0)
    projects_succeeded: Mapped[int | None] = mapped_column(Integer, default=0)
    projects_failed: Mapped[int | None] = mapped_column(Integer, default=0)
    projects_skipped: Mapped[int | None] = mapped_column(Integer, default=0)
    
    # QA summary (Point 27 integration)
    qa_flags_summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, doc="Aggregated QA flags from this run"
    )
    
    # Error tracking
    error_log: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, doc="Structured error log for failures"
    )
    
    # Resource usage
    total_requests: Mapped[int | None] = mapped_column(Integer)
    total_bytes_downloaded: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProjectPricingSnapshot(Base):
    """Price observation at a specific point in time."""

    __tablename__ = "project_pricing_snapshots"
    __table_args__ = (
        Index("ix_project_pricing_snapshots_project_date", "project_id", "snapshot_date"),
        Index("ix_project_pricing_snapshots_min_price", "min_price_total"),
        Index("ix_project_pricing_snapshots_max_price", "max_price_total"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    unit_type_label: Mapped[str | None] = mapped_column(String(100))
    min_price_total: Mapped[Numeric | None] = mapped_column(Numeric(14, 2))
    max_price_total: Mapped[Numeric | None] = mapped_column(Numeric(14, 2))
    min_price_per_sqft: Mapped[Numeric | None] = mapped_column(Numeric(10, 2))
    max_price_per_sqft: Mapped[Numeric | None] = mapped_column(Numeric(10, 2))
    
    # Enhancement #4: Price Per Sqft by Area Type
    price_per_sqft_carpet_min: Mapped[Numeric | None] = mapped_column(
        Numeric(10, 2), doc="Min price per sqft based on carpet area"
    )
    price_per_sqft_carpet_max: Mapped[Numeric | None] = mapped_column(
        Numeric(10, 2), doc="Max price per sqft based on carpet area"
    )
    price_per_sqft_sbua_min: Mapped[Numeric | None] = mapped_column(
        Numeric(10, 2), doc="Min price per sqft based on super builtup area"
    )
    price_per_sqft_sbua_max: Mapped[Numeric | None] = mapped_column(
        Numeric(10, 2), doc="Max price per sqft based on super builtup area"
    )
    
    source_type: Mapped[str | None] = mapped_column(String(50))
    source_reference: Mapped[str | None] = mapped_column(String(1024))
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="pricing_snapshots")


__all__ = [
    "Project",
    "Promoter",
    "Building",
    "UnitType",
    "ProjectDocument",
    "QuarterlyUpdate",
    "BankAccount",
    "LandParcel",
    "ProjectArtifact",
    "AmenityPOI",
    "ProjectAmenityStats",
    "ProjectScores",
    "ProjectLocation",
    "ProjectUnitType",
    "ProjectPricingSnapshot",
    # Point 28 & 29: Ops Standard
    "DataProvenance",
    "IngestionAudit",
]
