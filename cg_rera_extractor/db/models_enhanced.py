"""
Enhanced SQLAlchemy ORM models for the 10-Point Enhancement Standard.

This module contains NEW entities added to meet the enhancement requirements.
These should be imported alongside the existing models.py entities.

Enhancement Reference:
- #1: Developer Identity (Entity Promotion)
- #2: Hierarchy Restructuring (Project > Tower > Unit)
- #5: Structured Possession Timelines
- #7: Amenities Taxonomy
- #9: Transaction Registry
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
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
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from .enums import ProjectPhase, UnitStatus


# =============================================================================
# Enhancement #1: Developer Identity (Entity Promotion)
# =============================================================================

class Developer(Base):
    """
    First-class Developer entity with track record metrics.
    
    Enhancement #1: Developer Identity
    - Promotes developer from embedded string to proper entity
    - Enables trust scoring and historical tracking
    - One Developer can have many Projects
    """
    __tablename__ = "developers"
    __table_args__ = (
        UniqueConstraint("name", "state_code", name="uq_developer_name_state"),
        Index("ix_developers_trust_score", "trust_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Core identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state_code: Mapped[str | None] = mapped_column(String(10))
    legal_name: Mapped[str | None] = mapped_column(String(500))
    
    # Track record metrics
    estd_year: Mapped[int | None] = mapped_column(Integer, doc="Year of establishment")
    trust_score: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), 
        doc="Trust score 0-10 based on delivery history"
    )
    total_delivered_sqft: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        doc="Total square footage delivered across all projects"
    )
    total_projects_completed: Mapped[int | None] = mapped_column(Integer)
    total_projects_ongoing: Mapped[int | None] = mapped_column(Integer)
    
    # Contact & metadata
    headquarters_city: Mapped[str | None] = mapped_column(String(128))
    website: Mapped[str | None] = mapped_column(String(500))
    logo_url: Mapped[str | None] = mapped_column(String(1024))
    description: Mapped[str | None] = mapped_column(Text)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    
    # Relationships
    projects: Mapped[list["DeveloperProject"]] = relationship(
        back_populates="developer", cascade="all, delete-orphan"
    )


class DeveloperProject(Base):
    """
    Association table linking Developers to Projects.
    Allows tracking developer role (primary developer, JV partner, etc.)
    """
    __tablename__ = "developer_projects"
    __table_args__ = (
        UniqueConstraint("developer_id", "project_id", name="uq_developer_project"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    developer_id: Mapped[int] = mapped_column(
        ForeignKey("developers.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str | None] = mapped_column(
        String(50), 
        doc="Role: 'primary', 'jv_partner', 'construction_partner'"
    )
    ownership_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    
    developer: Mapped["Developer"] = relationship(back_populates="projects")
    # Note: Project relationship added via backref in main models.py


# Enhancement #2 was merged into the main Unit model in models.py to resolve conflicts.


# =============================================================================
# Enhancement #5: Structured Possession Timelines
# =============================================================================

class ProjectPossessionTimeline(Base):
    """
    Structured possession timeline per project or tower.
    
    Enhancement #5: Structured Possession Timelines
    - Replaces single possession_date with multiple timeline markers
    - Tracks marketing vs regulatory vs RERA deadlines
    - Supports phase tracking
    """
    __tablename__ = "project_possession_timelines"
    __table_args__ = (
        Index("ix_possession_timelines_project_id", "project_id"),
        Index("ix_possession_timelines_phase", "phase"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    building_id: Mapped[int | None] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE"),
        doc="Optional: timeline can be tower-specific"
    )
    
    # Timeline dates
    marketing_target: Mapped[date | None] = mapped_column(
        Date, doc="Date promised by sales/marketing team"
    )
    regulatory_deadline: Mapped[date | None] = mapped_column(
        Date, doc="Legal deadline per local regulations"
    )
    rera_deadline: Mapped[date | None] = mapped_column(
        Date, doc="RERA registered completion date"
    )
    actual_completion: Mapped[date | None] = mapped_column(
        Date, doc="Actual completion date (if completed)"
    )
    
    # Phase tracking
    phase: Mapped[str | None] = mapped_column(
        String(30),
        default=ProjectPhase.UNDER_CONSTRUCTION.value
    )
    phase_start_date: Mapped[date | None] = mapped_column(Date)
    
    # Delay tracking
    delay_months: Mapped[int | None] = mapped_column(
        Integer, 
        doc="Calculated delay from original RERA deadline"
    )
    delay_reason: Mapped[str | None] = mapped_column(String(500))
    
    # Metadata
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )


# =============================================================================
# Enhancement #7: Amenities Taxonomy
# =============================================================================

class AmenityCategory(Base):
    """
    Top-level amenity category (Health, Leisure, etc.)
    
    Enhancement #7: Amenities Taxonomy
    """
    __tablename__ = "amenity_categories"
    __table_args__ = (
        UniqueConstraint("code", name="uq_amenity_category_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    icon: Mapped[str | None] = mapped_column(String(50))
    display_order: Mapped[int | None] = mapped_column(Integer, default=0)
    lifestyle_weight: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2),
        doc="Weight for lifestyle score calculation (0-10)"
    )
    
    amenities: Mapped[list["Amenity"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class Amenity(Base):
    """
    Specific amenity (Pool, Gym, etc.) within a category.
    
    Enhancement #7: Amenities Taxonomy
    """
    __tablename__ = "amenities"
    __table_args__ = (
        UniqueConstraint("code", name="uq_amenity_code"),
        Index("ix_amenities_category_id", "category_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("amenity_categories.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    icon: Mapped[str | None] = mapped_column(String(50))
    lifestyle_points: Mapped[int | None] = mapped_column(
        Integer,
        doc="Points contributed to lifestyle score when present"
    )
    
    category: Mapped["AmenityCategory"] = relationship(back_populates="amenities")
    types: Mapped[list["AmenityType"]] = relationship(
        back_populates="amenity", cascade="all, delete-orphan"
    )


class AmenityType(Base):
    """
    Variant of an amenity (Indoor Pool, Outdoor Pool, etc.)
    
    Enhancement #7: Amenities Taxonomy
    """
    __tablename__ = "amenity_types"
    __table_args__ = (
        UniqueConstraint("amenity_id", "variant_code", name="uq_amenity_variant"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    amenity_id: Mapped[int] = mapped_column(
        ForeignKey("amenities.id", ondelete="CASCADE"), nullable=False
    )
    variant_code: Mapped[str] = mapped_column(String(50), nullable=False)
    variant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    premium_multiplier: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2),
        default=1.0,
        doc="Multiplier for lifestyle points (e.g., 1.5x for premium variants)"
    )
    
    amenity: Mapped["Amenity"] = relationship(back_populates="types")


class ProjectAmenity(Base):
    """
    Links projects to specific amenity types they offer.
    
    Enhancement #7: Amenities Taxonomy
    """
    __tablename__ = "project_amenities"
    __table_args__ = (
        UniqueConstraint("project_id", "amenity_type_id", name="uq_project_amenity_type"),
        Index("ix_project_amenities_project_id", "project_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    amenity_type_id: Mapped[int] = mapped_column(
        ForeignKey("amenity_types.id", ondelete="CASCADE"), nullable=False
    )
    
    # Status
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    is_chargeable: Mapped[bool | None] = mapped_column(Boolean)
    monthly_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    
    # Details
    quantity: Mapped[int | None] = mapped_column(Integer, default=1)
    size_sqft: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    details: Mapped[str | None] = mapped_column(String(500))
    images: Mapped[list[str] | None] = mapped_column(JSON)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# =============================================================================
# Enhancement #9: Transaction Registry (Verification Layer)
# =============================================================================

class TransactionHistory(Base):
    """
    Registry transaction records for verification.
    
    Enhancement #9: Transaction Registry
    - Stores actual property registration data
    - Enables market price validation
    - Buyer info is anonymized for privacy
    """
    __tablename__ = "transaction_history"
    __table_args__ = (
        Index("ix_transactions_project_id", "project_id"),
        Index("ix_transactions_registry_date", "registry_date"),
        Index("ix_transactions_price_sqft", "price_per_sqft_registered"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    building_id: Mapped[int | None] = mapped_column(
        ForeignKey("buildings.id", ondelete="SET NULL")
    )
    unit_id: Mapped[int | None] = mapped_column(
        ForeignKey("units.id", ondelete="SET NULL")
    )
    
    # Registry details
    registry_date: Mapped[date | None] = mapped_column(Date)
    registry_number: Mapped[str | None] = mapped_column(String(100))
    sub_registrar_office: Mapped[str | None] = mapped_column(String(255))
    
    # Transaction amounts
    declared_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        doc="Amount declared in registry"
    )
    stamp_duty_paid: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    registration_fee: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    
    # Area details
    registered_area_sqft: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    area_type: Mapped[str | None] = mapped_column(
        String(20),
        doc="carpet, builtup, or super_builtup"
    )
    
    # Derived metrics
    price_per_sqft_registered: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    
    # Privacy-compliant buyer info
    anonymized_buyer_hash: Mapped[str | None] = mapped_column(
        String(64),
        doc="SHA-256 hash of buyer PAN/Aadhaar for dedup without PII"
    )
    buyer_type: Mapped[str | None] = mapped_column(
        String(30),
        doc="individual, company, huf, nri"
    )
    
    # Source tracking
    source_type: Mapped[str | None] = mapped_column(String(50))
    source_reference: Mapped[str | None] = mapped_column(String(500))
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verification_status: Mapped[str | None] = mapped_column(String(30))
    
    # Relationships
    unit: Mapped["Unit"] = relationship(back_populates="transactions")


__all__ = [
    # Enhancement #1
    "Developer",
    "DeveloperProject",
    # Enhancement #2
    # "Unit",
    # Enhancement #5
    "ProjectPossessionTimeline",
    # Enhancement #7
    "AmenityCategory",
    "Amenity",
    "AmenityType",
    "ProjectAmenity",
    # Enhancement #9
    "TransactionHistory",
]
