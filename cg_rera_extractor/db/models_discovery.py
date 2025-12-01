"""
Discovery & Trust Layer Models (Points 24-26)

This module contains models for:
- Point 24: Structured Locality Tags (Faceted Search)
- Point 25: RERA Verification System
- Point 26: Entity Enrichment & Knowledge Graph (Landmarks)
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
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
from .enums import TagCategory, ReraVerificationStatus


# =============================================================================
# Point 24: Structured Locality Tags (Faceted Search)
# =============================================================================

class Tag(Base):
    """
    Tag entity for faceted search filtering.
    
    Point 24: Structured Locality Tags
    - Enables checkbox-based filtering instead of text search
    - Categories: PROXIMITY, INFRASTRUCTURE, INVESTMENT, LIFESTYLE, CERTIFICATION
    - Auto-generated tags (e.g., distance-based) vs manual tags
    """
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_tags_slug"),
        Index("ix_tags_category", "category"),
        Index("ix_tags_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Tag identity
    slug: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        doc="URL-friendly unique identifier (e.g., 'metro-connected')"
    )
    name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        doc="Human-readable display name (e.g., 'Metro Connected')"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        doc="Explanation of what this tag means"
    )
    
    # Classification
    category: Mapped[TagCategory] = mapped_column(
        Enum(TagCategory),
        nullable=False,
        doc="Tag category for grouping in UI"
    )
    
    # Auto-tagging configuration
    is_auto_generated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="True if tag is computed (e.g., proximity-based)"
    )
    auto_rule_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        doc="Rule definition for auto-tagging (e.g., {'type': 'proximity', 'target': 'metro', 'max_km': 2})"
    )
    
    # Display
    icon_emoji: Mapped[str | None] = mapped_column(String(10))
    color_hex: Mapped[str | None] = mapped_column(String(7), doc="e.g., #3B82F6")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, doc="Show in top filters")
    
    # SEO
    seo_title: Mapped[str | None] = mapped_column(String(255))
    seo_description: Mapped[str | None] = mapped_column(String(500))
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    
    # Relationships
    project_tags: Mapped[list["ProjectTag"]] = relationship(
        back_populates="tag", cascade="all, delete-orphan"
    )


class ProjectTag(Base):
    """
    Many-to-many join table between Projects and Tags.
    
    Point 24: Allows a project to have multiple tags and tracks
    how/when the tag was applied (auto vs manual).
    """
    __tablename__ = "project_tags"
    __table_args__ = (
        UniqueConstraint("project_id", "tag_id", name="uq_project_tag"),
        Index("ix_project_tags_project_id", "project_id"),
        Index("ix_project_tags_tag_id", "tag_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Tagging metadata
    is_auto_applied: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        doc="True if applied by auto-tagging service"
    )
    confidence_score: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 3),
        doc="Confidence of auto-tagging (0.0-1.0)"
    )
    applied_by: Mapped[str | None] = mapped_column(
        String(100),
        doc="User or system that applied the tag"
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    # For proximity tags
    computed_distance_km: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 2),
        doc="Distance to target if proximity-based tag"
    )
    
    # Relationships
    tag: Mapped["Tag"] = relationship(back_populates="project_tags")


# =============================================================================
# Point 25: RERA Verification System
# =============================================================================

class ReraVerification(Base):
    """
    RERA verification history and status tracking.
    
    Point 25: The Trust Badge
    - Tracks verification status over time
    - Stores official portal link
    - Records verification timestamps
    
    This is a separate table to maintain history and allow
    periodic re-verification without losing old data.
    """
    __tablename__ = "rera_verifications"
    __table_args__ = (
        Index("ix_rera_verifications_project_id", "project_id"),
        Index("ix_rera_verifications_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Verification state
    status: Mapped[ReraVerificationStatus] = mapped_column(
        Enum(ReraVerificationStatus),
        nullable=False,
        default=ReraVerificationStatus.UNKNOWN
    )
    
    # Official links
    official_record_url: Mapped[str | None] = mapped_column(
        String(1024),
        doc="Direct URL to government RERA portal page for this project"
    )
    portal_screenshot_url: Mapped[str | None] = mapped_column(
        String(1024),
        doc="Archived screenshot of portal page for evidence"
    )
    
    # Registration details from portal
    registered_name_on_portal: Mapped[str | None] = mapped_column(
        String(500),
        doc="Project name as it appears on RERA portal"
    )
    promoter_name_on_portal: Mapped[str | None] = mapped_column(
        String(500),
        doc="Promoter name on RERA portal for cross-check"
    )
    portal_registration_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        doc="Registration date per portal"
    )
    portal_expiry_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        doc="Registration expiry date per portal"
    )
    
    # Verification metadata
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        doc="When this verification check was performed"
    )
    verified_by: Mapped[str | None] = mapped_column(
        String(100),
        doc="System or user that performed verification"
    )
    verification_method: Mapped[str | None] = mapped_column(
        String(50),
        doc="How verification was done: 'scraper', 'api', 'manual'"
    )
    
    # Discrepancy tracking
    has_discrepancies: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="True if our data doesn't match portal"
    )
    discrepancy_notes: Mapped[str | None] = mapped_column(
        Text,
        doc="Details of any mismatches found"
    )
    
    # Raw response
    raw_portal_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        doc="Raw data scraped from portal for audit"
    )
    
    # Is this the current/latest verification?
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        doc="True for the most recent verification record"
    )


# =============================================================================
# Point 26: Entity Enrichment - Landmarks
# =============================================================================

class Landmark(Base):
    """
    Named landmark entity for knowledge graph linking.
    
    Point 26: Entity Enrichment
    - Promotes common landmarks (malls, tech parks, stations) to entities
    - Enables "Near Phoenix Mall" to be a link, not just text
    - SEO benefit through internal linking
    """
    __tablename__ = "landmarks"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_landmarks_slug"),
        Index("ix_landmarks_category", "category"),
        Index("ix_landmarks_lat_lon", "lat", "lon"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identity
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="URL-friendly identifier (e.g., 'phoenix-mall-pune')"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    alternate_names: Mapped[list[str] | None] = mapped_column(
        JSON,
        doc="Other names this landmark is known by"
    )
    
    # Classification
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type: mall, tech_park, metro_station, airport, hospital, school, etc."
    )
    subcategory: Mapped[str | None] = mapped_column(
        String(50),
        doc="More specific type, e.g., 'it_park' under 'tech_park'"
    )
    
    # Location
    lat: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    lon: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    address: Mapped[str | None] = mapped_column(String(512))
    city: Mapped[str | None] = mapped_column(String(128))
    district: Mapped[str | None] = mapped_column(String(128))
    state: Mapped[str | None] = mapped_column(String(128))
    
    # Metadata
    established_year: Mapped[int | None] = mapped_column(Integer)
    website: Mapped[str | None] = mapped_column(String(500))
    image_url: Mapped[str | None] = mapped_column(String(1024))
    description: Mapped[str | None] = mapped_column(Text)
    
    # Importance for auto-tagging
    importance_score: Mapped[int] = mapped_column(
        Integer,
        default=50,
        doc="0-100 score for prioritizing in auto-tagging"
    )
    default_proximity_km: Mapped[Decimal] = mapped_column(
        Numeric(4, 1),
        default=5.0,
        doc="Default radius for 'near X' calculations"
    )
    
    # SEO
    seo_title: Mapped[str | None] = mapped_column(String(255))
    seo_description: Mapped[str | None] = mapped_column(String(500))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    
    # Relationships
    project_landmarks: Mapped[list["ProjectLandmark"]] = relationship(
        back_populates="landmark", cascade="all, delete-orphan"
    )


class ProjectLandmark(Base):
    """
    Many-to-many: Projects near Landmarks.
    
    Point 26: Enables queries like:
    - "All projects near Phoenix Mall"
    - "This project is near: Metro Station, IT Park, Mall"
    """
    __tablename__ = "project_landmarks"
    __table_args__ = (
        UniqueConstraint("project_id", "landmark_id", name="uq_project_landmark"),
        Index("ix_project_landmarks_project_id", "project_id"),
        Index("ix_project_landmarks_landmark_id", "landmark_id"),
        Index("ix_project_landmarks_distance", "distance_km"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    landmark_id: Mapped[int] = mapped_column(
        ForeignKey("landmarks.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Distance data
    distance_km: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        doc="Straight-line distance in km"
    )
    driving_time_mins: Mapped[int | None] = mapped_column(
        Integer,
        doc="Estimated driving time in minutes"
    )
    walking_time_mins: Mapped[int | None] = mapped_column(
        Integer,
        doc="Estimated walking time in minutes"
    )
    
    # Display preferences
    is_highlighted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="Show prominently in project listing"
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Calculation metadata
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    landmark: Mapped["Landmark"] = relationship(back_populates="project_landmarks")


__all__ = [
    # Point 24
    "Tag",
    "ProjectTag",
    # Point 25
    "ReraVerification",
    # Point 26
    "Landmark",
    "ProjectLandmark",
]
