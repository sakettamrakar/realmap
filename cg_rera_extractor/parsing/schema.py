"""Data models for raw extracted data and the normalized V1 scraper schema."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FieldRecord(BaseModel):
    """Represents a label/value pair extracted from a section of the detail page."""

    label: str = Field(..., description="Label as extracted from the HTML.")
    value: Optional[str] = Field(default=None, description="Extracted text or URL value.")
    value_type: Optional[str] = Field(
        default=None,
        description="Classifier output describing the field value type (text/date/url/etc).",
    )


class SectionRecord(BaseModel):
    """Container for a list of :class:`FieldRecord` entries under a section heading."""

    section_title_raw: str = Field(..., description="Section title exactly as found on the page.")
    fields: List[FieldRecord] = Field(default_factory=list, description="Field records extracted from the section.")


class RawExtractedProject(BaseModel):
    """Raw extracted representation of a CG RERA project detail page."""

    registration_number: Optional[str] = Field(
        default=None,
        description="Project registration number captured from the header area.",
    )
    project_name: Optional[str] = Field(
        default=None,
        description="Project name captured from the header area.",
    )
    source_url: Optional[str] = Field(default=None, description="URL of the project detail page.")
    scraped_at: Optional[datetime] = Field(
        default=None, description="Timestamp indicating when the page was scraped."
    )
    sections: List[SectionRecord] = Field(
        default_factory=list,
        description="List of sections parsed from the detail page.",
    )


class V1Metadata(BaseModel):
    """Metadata associated with a normalized V1 scraper record."""

    schema_version: str = Field(default="1.0", description="Version of the scraper JSON schema.")
    state_code: str = Field(..., description="Two-letter state code (CG for Chhattisgarh).")
    source_url: Optional[str] = Field(default=None, description="Original project detail URL.")
    scraped_at: Optional[datetime] = Field(default=None, description="Timestamp when the project was scraped.")


class V1ProjectDetails(BaseModel):
    """Canonical project level attributes."""

    registration_number: Optional[str] = Field(default=None, description="Official CG RERA registration number.")
    project_name: Optional[str] = Field(default=None, description="Name of the project as registered with CG RERA.")
    project_type: Optional[str] = Field(default=None, description="Project type (Residential/Commercial/etc).")
    project_status: Optional[str] = Field(default=None, description="Current status reported to CG RERA.")
    district: Optional[str] = Field(default=None, description="District where the project is located.")
    tehsil: Optional[str] = Field(default=None, description="Tehsil where the project is located.")
    project_address: Optional[str] = Field(default=None, description="Full postal address of the project site.")
    total_units: Optional[int] = Field(default=None, description="Total number of units registered under the project.")
    total_area_sq_m: Optional[float] = Field(default=None, description="Total project area in square metres.")
    launch_date: Optional[str] = Field(default=None, description="Project launch date (as reported).")
    expected_completion_date: Optional[str] = Field(
        default=None, description="Expected completion date provided to CG RERA."
    )


class V1PromoterDetails(BaseModel):
    """Information about a promoter associated with the project."""

    name: Optional[str] = Field(default=None, description="Promoter name.")
    organisation_type: Optional[str] = Field(default=None, description="Type of entity (individual/company/etc).")
    address: Optional[str] = Field(default=None, description="Registered address of the promoter.")
    email: Optional[str] = Field(default=None, description="Primary email of the promoter.")
    phone: Optional[str] = Field(default=None, description="Primary contact number of the promoter.")
    pan: Optional[str] = Field(default=None, description="Permanent Account Number (if available).")
    cin: Optional[str] = Field(default=None, description="Corporate Identification Number (if available).")


class V1LandDetails(BaseModel):
    """Details of the land parcel on which the project stands."""

    land_area_sq_m: Optional[float] = Field(default=None, description="Total land area in square metres.")
    land_status: Optional[str] = Field(default=None, description="Ownership or acquisition status of the land.")
    land_address: Optional[str] = Field(default=None, description="Address/location description of the land parcel.")
    khasra_numbers: Optional[str] = Field(default=None, description="Reported khasra/survey numbers.")


class V1BuildingDetails(BaseModel):
    """Summary of a building/tower/block under the project."""

    name: Optional[str] = Field(default=None, description="Name or identifier of the building.")
    number_of_floors: Optional[int] = Field(default=None, description="Number of floors registered for the building.")
    number_of_units: Optional[int] = Field(default=None, description="Units associated with the building.")
    carpet_area_sq_m: Optional[float] = Field(default=None, description="Carpet area of the building in square metres.")


class V1UnitType(BaseModel):
    """Normalized representation of a unit type (1BHK/Shop/etc)."""

    name: Optional[str] = Field(default=None, description="Unit type name or configuration.")
    carpet_area_sq_m: Optional[float] = Field(default=None, description="Carpet area in square metres.")
    built_up_area_sq_m: Optional[float] = Field(default=None, description="Built-up area in square metres.")
    price_in_inr: Optional[float] = Field(default=None, description="Indicative price in INR for the unit type.")


class V1BankDetails(BaseModel):
    """Information about escrow/bank accounts declared for the project."""

    bank_name: Optional[str] = Field(default=None, description="Name of the bank maintaining the escrow account.")
    branch_name: Optional[str] = Field(default=None, description="Branch name/location.")
    account_number: Optional[str] = Field(default=None, description="Account number as reported.")
    ifsc_code: Optional[str] = Field(default=None, description="IFSC code for the bank/branch.")


class V1Document(BaseModel):
    """Document metadata for files linked on the detail page."""

    name: Optional[str] = Field(default=None, description="Document name or description.")
    document_type: Optional[str] = Field(default=None, description="Type/category of the uploaded document.")
    url: Optional[str] = Field(default=None, description="Absolute URL to download the document.")
    uploaded_on: Optional[str] = Field(default=None, description="Upload date reported by the portal.")


class V1QuarterlyUpdate(BaseModel):
    """Quarterly progress update filed with CG RERA."""

    quarter: Optional[str] = Field(default=None, description="Quarter label (Q1/Q2/etc).")
    year: Optional[str] = Field(default=None, description="Calendar year for the update.")
    status: Optional[str] = Field(default=None, description="Status description provided in the update.")
    completion_percent: Optional[float] = Field(default=None, description="Completion percentage reported.")
    remarks: Optional[str] = Field(default=None, description="Additional remarks for the quarter.")


class V1RawData(BaseModel):
    """Helper structure for storing canonicalized and unmapped data."""

    sections: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="Canonical section-to-field mapping used to build the V1 model.",
    )
    unmapped_sections: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="Raw sections/fields that did not map to a canonical location.",
    )


class V1Project(BaseModel):
    """Top-level V1 scraper JSON structure."""

    metadata: V1Metadata
    project_details: V1ProjectDetails
    promoter_details: List[V1PromoterDetails] = Field(default_factory=list)
    land_details: List[V1LandDetails] = Field(default_factory=list)
    building_details: List[V1BuildingDetails] = Field(default_factory=list)
    unit_types: List[V1UnitType] = Field(default_factory=list)
    bank_details: List[V1BankDetails] = Field(default_factory=list)
    documents: List[V1Document] = Field(default_factory=list)
    quarterly_updates: List[V1QuarterlyUpdate] = Field(default_factory=list)
    raw_data: V1RawData = Field(default_factory=V1RawData)


__all__ = [
    "FieldRecord",
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
    "V1RawData",
    "V1Project",
]
