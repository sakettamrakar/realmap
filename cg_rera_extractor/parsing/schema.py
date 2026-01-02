"""Data models used by the parsing and mapping layers."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FieldValueType(str, Enum):
    """Enumeration of supported raw field value classifications."""

    TEXT = "TEXT"
    NUMBER = "NUMBER"
    DATE = "DATE"
    URL = "URL"
    UNKNOWN = "UNKNOWN"


class FieldRecord(BaseModel):
    """Represents a single label/value pair extracted from the HTML."""

    label: str
    value: Optional[str] = None
    value_type: FieldValueType = Field(default=FieldValueType.TEXT)
    links: list[str] = Field(default_factory=list)
    preview_present: bool = False
    preview_hint: Optional[str] = None


class TableRecord(BaseModel):
    """Represents a data table extracted from a section."""
    
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)


class GridRecord(BaseModel):
    """Represents a visual grid (like inventory status) extracted from a section."""
    
    items: list[dict[str, str]] = Field(default_factory=list)
    legend: dict[str, str] = Field(default_factory=dict)


class SectionRecord(BaseModel):
    """Collection of fields grouped under the same section heading."""

    section_title_raw: str
    fields: list[FieldRecord] = Field(default_factory=list)
    tables: list[TableRecord] = Field(default_factory=list)
    grids: list[GridRecord] = Field(default_factory=list)


class RawExtractedProject(BaseModel):
    """Top-level structure returned by the HTML parser."""

    registration_number: Optional[str] = None
    project_name: Optional[str] = None
    source_url: Optional[str] = None
    scraped_at: Optional[str] = None
    source_file: Optional[str] = None
    sections: list[SectionRecord] = Field(default_factory=list)


class V1Metadata(BaseModel):
    """Metadata block for the V1 scraper schema."""

    schema_version: str = "1.0"
    state_code: str
    source_url: Optional[str] = None
    scraped_at: Optional[str] = None


class V1ProjectDetails(BaseModel):
    """Normalized project details."""

    registration_number: Optional[str] = None
    project_name: Optional[str] = None
    project_type: Optional[str] = None
    project_status: Optional[str] = None
    district: Optional[str] = None
    tehsil: Optional[str] = None
    village_or_locality: Optional[str] = None
    pincode: Optional[str] = None
    project_address: Optional[str] = None
    project_website_url: Optional[str] = None  # Website URL from listing page
    total_units: Optional[int] = None
    total_area_sq_m: Optional[float] = None
    launch_date: Optional[str] = None
    expected_completion_date: Optional[str] = None


class V1PromoterDetails(BaseModel):
    """Normalized promoter details."""

    name: Optional[str] = None
    organisation_type: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    pan: Optional[str] = None
    cin: Optional[str] = None


class V1LandDetails(BaseModel):
    land_area_sq_m: Optional[float] = None
    land_status: Optional[str] = None
    land_address: Optional[str] = None
    khasra_numbers: Optional[str] = None


class V1BuildingDetails(BaseModel):
    name: Optional[str] = None
    number_of_floors: Optional[int] = None
    number_of_units: Optional[int] = None
    carpet_area_sq_m: Optional[float] = None


class V1UnitType(BaseModel):
    name: Optional[str] = None
    carpet_area_sq_m: Optional[float] = None
    built_up_area_sq_m: Optional[float] = None
    super_built_up_area_sq_m: Optional[float] = None
    balcony_area_sq_m: Optional[float] = None
    common_area_sq_m: Optional[float] = None
    terrace_area_sq_m: Optional[float] = None
    price_in_inr: Optional[float] = None


class V1BankDetails(BaseModel):
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None


class V1Document(BaseModel):
    name: Optional[str] = None
    document_type: Optional[str] = None
    url: Optional[str] = None
    uploaded_on: Optional[str] = None


class V1QuarterlyUpdate(BaseModel):
    quarter: Optional[str] = None
    year: Optional[str] = None
    status: Optional[str] = None
    completion_percent: Optional[float] = None
    remarks: Optional[str] = None


class V1ReraLocation(BaseModel):
    """A location point captured from RERA detail page (amenities or map marker)."""

    source_type: str  # e.g., "amenity", "map_marker", "project_pin"
    latitude: float
    longitude: float
    particulars: Optional[str] = None  # e.g., "INTERNAL ROADS AND FOOTPATHS"
    image_url: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    progress_percent: Optional[float] = None


class PreviewArtifact(BaseModel):
    """Represents captured artifacts for a preview-enabled field."""

    field_key: str
    artifact_type: str = "unknown"
    files: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class V1RawData(BaseModel):
    sections: dict[str, dict[str, str]] = Field(default_factory=dict)
    tables: dict[str, list[TableRecord]] = Field(default_factory=dict)
    grids: dict[str, list[GridRecord]] = Field(default_factory=dict)
    unmapped_sections: dict[str, dict[str, str]] = Field(default_factory=dict)


class V1Project(BaseModel):
    metadata: V1Metadata
    project_details: V1ProjectDetails
    promoter_details: list[V1PromoterDetails] = Field(default_factory=list)
    land_details: list[V1LandDetails] = Field(default_factory=list)
    building_details: list[V1BuildingDetails] = Field(default_factory=list)
    unit_types: list[V1UnitType] = Field(default_factory=list)
    bank_details: list[V1BankDetails] = Field(default_factory=list)
    documents: list[V1Document] = Field(default_factory=list)
    quarterly_updates: list[V1QuarterlyUpdate] = Field(default_factory=list)
    rera_locations: list[V1ReraLocation] = Field(default_factory=list)  # Amenity/map lat/lon
    raw_data: V1RawData
    validation_messages: list[str] = Field(default_factory=list)
    previews: dict[str, PreviewArtifact] = Field(default_factory=dict)


__all__ = [
    "FieldRecord",
    "FieldValueType",
    "SectionRecord",
    "RawExtractedProject",
    "V1Metadata",
    "V1ProjectDetails",
    "V1PromoterDetails",
    "V1LandDetails",
    "V1BuildingDetails",
    "V1UnitType",
    "V1BankDetails",
    "V1Document",
    "V1QuarterlyUpdate",
    "V1ReraLocation",
    "V1RawData",
    "V1Project",
    "PreviewArtifact",
]
