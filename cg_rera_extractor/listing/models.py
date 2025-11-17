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
    run_id: str | None = None
    row_index: int | None = None
