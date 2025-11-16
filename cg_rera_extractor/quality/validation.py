"""Validation helpers for normalized V1 projects."""
from __future__ import annotations

import re

from cg_rera_extractor.parsing.schema import V1Project


def _validate_pincode(raw_value: str | None) -> str | None:
    if not raw_value:
        return None
    digits = re.sub(r"\D", "", raw_value)
    if not digits:
        return None
    if len(digits) != 6:
        return "Invalid pincode format (expected 6 digits)."
    return None


def validate_v1_project(project: V1Project) -> list[str]:
    """Return a list of validation messages (warnings/errors)."""

    messages: list[str] = []
    details = project.project_details

    if not details.district:
        messages.append("Missing district in project details.")
    if not details.project_status:
        messages.append("Missing project status in project details.")

    raw_pincode = project.raw_data.sections.get("project_details", {}).get("pincode")
    pincode_message = _validate_pincode(raw_pincode)
    if pincode_message:
        messages.append(pincode_message)

    for idx, land in enumerate(project.land_details, start=1):
        if land.land_area_sq_m is not None and land.land_area_sq_m <= 0:
            messages.append(
                f"Land detail {idx}: land_area_sq_m should be a positive number."
            )

    if details.total_area_sq_m is not None and details.total_area_sq_m <= 0:
        messages.append("Project total_area_sq_m should be a positive number.")

    return messages


__all__ = ["validate_v1_project"]
