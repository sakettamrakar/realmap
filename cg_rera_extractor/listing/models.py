"""Data models for CG RERA listing pages."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ListingRecord:
    """Single entry returned from the CG RERA listing search table."""

    reg_no: str
    project_name: str
    promoter_name: str | None = None
    district: str | None = None
    tehsil: str | None = None
    status: str | None = None
    detail_url: str = ""
    website_url: str | None = None  # Project website URL from listing page
    map_latitude: float | None = None  # Latitude from listing page map popup
    map_longitude: float | None = None  # Longitude from listing page map popup
    run_id: str | None = None
    row_index: int | None = None
