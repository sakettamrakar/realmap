"""Pydantic models for API responses."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Promoter(BaseModel):
    """Promoter information for a project."""

    model_config = ConfigDict(from_attributes=True)

    promoter_name: str
    promoter_type: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    website: str | None = None


class Building(BaseModel):
    """Building/tower level details."""

    model_config = ConfigDict(from_attributes=True)

    building_name: str
    building_type: str | None = None
    number_of_floors: int | None = None
    total_units: int | None = None
    status: str | None = None


class UnitType(BaseModel):
    """Unit type mix for a project."""

    model_config = ConfigDict(from_attributes=True)

    type_name: str
    carpet_area_sqmt: Decimal | None = None
    saleable_area_sqmt: Decimal | None = None
    total_units: int | None = None
    sale_price: Decimal | None = None


class ProjectDocument(BaseModel):
    """Documents associated with a project."""

    model_config = ConfigDict(from_attributes=True)

    doc_type: str | None = None
    description: str | None = None
    url: str | None = None


class QuarterlyUpdate(BaseModel):
    """Quarterly progress updates."""

    model_config = ConfigDict(from_attributes=True)

    quarter: str | None = None
    update_date: date | None = None
    status: str | None = None
    summary: str | None = None
    raw_data_json: dict[str, Any] | None = None


class ProjectSummary(BaseModel):
    """Lightweight projection for list endpoint."""

    model_config = ConfigDict(from_attributes=True)

    state_code: str
    rera_registration_number: str
    project_name: str
    status: str | None = None
    district: str | None = None
    tehsil: str | None = None
    village_or_locality: str | None = None
    normalized_address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    approved_date: date | None = None
    proposed_end_date: date | None = None
    extended_end_date: date | None = None


class ProjectDetail(ProjectSummary):
    """Full project details including nested relations."""

    full_address: str | None = None
    pincode: str | None = None
    geocoding_status: str | None = None
    geocoding_source: str | None = None
    raw_data_json: dict[str, Any] | None = None
    promoters: list[Promoter] = Field(default_factory=list)
    buildings: list[Building] = Field(default_factory=list)
    unit_types: list[UnitType] = Field(default_factory=list)
    documents: list[ProjectDocument] = Field(default_factory=list)
    quarterly_updates: list[QuarterlyUpdate] = Field(default_factory=list)
