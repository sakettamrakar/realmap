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
    score: Mapped["ProjectScores" | None] = relationship(
        back_populates="project", cascade="all, delete-orphan", uselist=False
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
    radius_km: Mapped[Numeric] = mapped_column(Numeric(4, 2), nullable=False)
    count_within_radius: Mapped[int | None] = mapped_column(Integer)
    nearest_distance_km: Mapped[Numeric | None] = mapped_column(Numeric(6, 3))
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
    connectivity_score: Mapped[int | None] = mapped_column(Integer)
    daily_needs_score: Mapped[int | None] = mapped_column(Integer)
    social_infra_score: Mapped[int | None] = mapped_column(Integer)
    overall_score: Mapped[int | None] = mapped_column(Integer)
    score_version: Mapped[str | None] = mapped_column(String(32))
    last_computed_at: Mapped[date | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project] = relationship(back_populates="score")


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
]
