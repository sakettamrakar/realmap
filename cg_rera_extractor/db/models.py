"""SQLAlchemy ORM models for CG RERA projects."""
from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, UniqueConstraint
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
    pincode: Mapped[str | None] = mapped_column(String(20))
    latitude: Mapped[Numeric | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Numeric | None] = mapped_column(Numeric(9, 6))
    geocoding_status: Mapped[str | None] = mapped_column(String(64))
    geocoding_source: Mapped[str | None] = mapped_column(String(64))
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
]
