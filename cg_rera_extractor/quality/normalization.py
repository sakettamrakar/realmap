"""Normalization helpers for V1Project objects."""
from __future__ import annotations

import re
from typing import Dict

from cg_rera_extractor.parsing.schema import V1Project


_DISTRICT_MAP: Dict[str, str] = {
    "raipur": "Raipur",
    "bilaspur": "Bilaspur",
    "durg": "Durg",
    "korba": "Korba",
    "dhamtari": "Dhamtari",
    "rajnandgaon": "Rajnandgaon",
}

_STATUS_MAP: Dict[str, str] = {
    "ongoing": "Ongoing",
    "on-going": "Ongoing",
    "on going": "Ongoing",
    "registered": "Registered",
    "registration": "Registered",
    "completed": "Completed",
}

_PROJECT_TYPE_MAP: Dict[str, str] = {
    "residential": "Residential",
    "commercial": "Commercial",
    "mixed use": "Mixed Use",
    "mixed-use": "Mixed Use",
    "residential and commercial": "Residential and Commercial",
    "residential & commercial": "Residential and Commercial",
}


def _clean_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def normalize_district(name: str | None) -> str:
    """Normalize district names into title case with known mappings."""

    cleaned = _clean_whitespace(name)
    key = cleaned.lower()
    if not key:
        return ""
    return _DISTRICT_MAP.get(key, cleaned.title())


def normalize_status(status: str | None) -> str:
    """Normalize project status strings using simple mappings."""

    cleaned = _clean_whitespace(status)
    key = cleaned.lower()
    if not key:
        return ""
    return _STATUS_MAP.get(key, cleaned.title())


def normalize_project_type(ptype: str | None) -> str:
    """Normalize project type labels to a canonical representation."""

    cleaned = _clean_whitespace(ptype)
    key = cleaned.lower()
    if not key:
        return ""
    return _PROJECT_TYPE_MAP.get(key, cleaned.title())


def clean_reg_no(reg: str | None) -> str:
    """Strip noise from registration numbers and uppercase them."""

    cleaned = _clean_whitespace(reg)
    if not cleaned:
        return ""
    compact = re.sub(r"\s+", "", cleaned)
    compact = re.sub(r"-+", "-", compact)
    return compact.upper().strip("-./")


def normalize_v1_project(project: V1Project) -> V1Project:
    """Return a normalized copy of the provided V1 project."""

    normalized_details = project.project_details.model_copy()
    normalized_details.district = normalize_district(normalized_details.district)
    normalized_details.project_status = normalize_status(
        normalized_details.project_status
    )
    normalized_details.project_type = normalize_project_type(
        normalized_details.project_type
    )
    normalized_details.registration_number = clean_reg_no(
        normalized_details.registration_number
    )
    normalized_details.project_name = _clean_whitespace(normalized_details.project_name)
    normalized_details.project_address = _clean_whitespace(
        normalized_details.project_address
    )

    return project.model_copy(update={"project_details": normalized_details})


__all__ = [
    "clean_reg_no",
    "normalize_district",
    "normalize_status",
    "normalize_project_type",
    "normalize_v1_project",
]
