"""Data models for CG RERA listing records."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ListingRecord:
    """Represents a single project listing returned by the CG RERA portal."""

    reg_no: str
    project_name: str
    promoter_name: str
    district: str
    tehsil: str
    status: str
    detail_url: str
    run_id: str

