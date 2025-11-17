from __future__ import annotations

import re
from typing import Dict, List, TypedDict

from cg_rera_extractor.parsing.schema import V1Project


class FieldDiff(TypedDict):
    field_key: str
    json_value: str | None
    html_value: str | None
    status: str  # "match" | "mismatch" | "missing_in_html" | "missing_in_json" | "preview_unchecked"
    notes: str | None


FIELD_MAPPING: Dict[str, str] = {
    "project_details.registration_number": "registration_number",
    "project_details.project_name": "project_name",
    "project_details.project_type": "project_type",
    "project_details.project_status": "project_status",
    "project_details.district": "district",
    "project_details.tehsil": "tehsil",
    "project_details.project_address": "project_address",
    "project_details.launch_date": "launch_date",
    "project_details.expected_completion_date": "expected_completion_date",
}


SPACE_RE = re.compile(r"\s+")


def _normalize_value(value: str | None) -> str:
    if value is None:
        return ""
    collapsed = SPACE_RE.sub(" ", str(value)).strip()
    return collapsed


def _extract_json_value(obj: object, path: str) -> str | None:
    current: object = obj
    for part in path.split("."):
        index = None
        if "[" in part and part.endswith("]"):
            name, index_str = part[:-1].split("[")
            part = name
            try:
                index = int(index_str)
            except ValueError:
                index = None

        if not hasattr(current, part):
            return None
        current = getattr(current, part)

        if index is not None:
            if not isinstance(current, list) or len(current) <= index:
                return None
            current = current[index]

    if current is None:
        return None

    if isinstance(current, (list, dict)):
        return None

    return str(current)


def compare_v1_to_html_fields(v1: V1Project, html_fields: Dict[str, str]) -> List[FieldDiff]:
    """
    Compare every mapped field in V1Project to the extracted HTML fields.
    """

    diffs: List[FieldDiff] = []

    for json_path, html_key in FIELD_MAPPING.items():
        json_raw = _extract_json_value(v1, json_path)
        html_raw = html_fields.get(html_key)

        normalized_json = _normalize_value(json_raw)
        normalized_html = _normalize_value(html_raw)

        status: str
        notes: str | None = None

        if json_raw is None:
            status = "missing_in_json"
        elif html_raw is None:
            status = "missing_in_html"
        elif normalized_json.lower() == "preview" or normalized_html.lower() == "preview":
            status = "preview_unchecked"
        elif normalized_json.lower() != normalized_html.lower():
            status = "mismatch"
        else:
            status = "match"

        diffs.append(
            FieldDiff(
                field_key=json_path,
                json_value=normalized_json if normalized_json else None,
                html_value=normalized_html if normalized_html else None,
                status=status,
                notes=notes,
            )
        )

    return diffs
