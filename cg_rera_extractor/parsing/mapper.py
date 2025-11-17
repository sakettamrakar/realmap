"""Utilities for mapping raw extracted data to the V1 scraper schema."""
from __future__ import annotations

import json
import re
from importlib import resources
from typing import Dict, Tuple

from .schema import (
    PreviewArtifact,
    RawExtractedProject,
    V1BankDetails,
    V1BuildingDetails,
    V1Document,
    V1LandDetails,
    V1Metadata,
    V1Project,
    V1ProjectDetails,
    V1PromoterDetails,
    V1QuarterlyUpdate,
    V1RawData,
    V1UnitType,
)

_LOGICAL_SECTIONS_RESOURCE = "logical_sections_and_keys.json"


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _load_logical_section_mapping() -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
    resource = resources.files("cg_rera_extractor.parsing.data").joinpath(
        _LOGICAL_SECTIONS_RESOURCE
    )
    data = json.loads(resource.read_text("utf-8"))

    title_lookup: Dict[str, str] = {}
    key_lookup: Dict[str, Dict[str, str]] = {}
    for section in data.get("sections", []):
        logical_name = section["logical_section"]
        section_titles = section.get("section_title_variants", [])
        for title in section_titles:
            title_lookup[_normalize(title)] = logical_name
        canonical_map: Dict[str, str] = {}
        for canonical_key, variants in section.get("keys", {}).items():
            for variant in variants:
                canonical_map[_normalize(variant)] = canonical_key
        key_lookup[logical_name] = canonical_map

    return title_lookup, key_lookup


_SECTION_LOOKUP, _KEY_LOOKUP = _load_logical_section_mapping()


def _to_int(value: str | None) -> int | None:
    if not value:
        return None
    digits = re.sub(r"[^0-9]", "", value)
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _to_float(value: str | None) -> float | None:
    if not value:
        return None
    cleaned = value.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        match = re.search(r"[0-9]+(?:\.[0-9]+)?", cleaned)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
    return None


def map_raw_to_v1(raw: RawExtractedProject, state_code: str = "CG") -> V1Project:
    """Map a :class:`RawExtractedProject` into the V1 scraper schema."""

    section_data: Dict[str, Dict[str, str]] = {}
    unmapped_sections: Dict[str, Dict[str, str]] = {}
    previews: Dict[str, PreviewArtifact] = {}

    for section in raw.sections:
        normalized_title = _normalize(section.section_title_raw)
        logical_section = _SECTION_LOOKUP.get(normalized_title)
        if not logical_section:
            target = unmapped_sections.setdefault(section.section_title_raw, {})
            for field in section.fields:
                if field.label:
                    target[field.label] = field.value or ""
                    # Capture preview placeholders for unmapped section fields
                    if field.preview_present:
                        field_key = _normalize(field.label)
                        if field_key not in previews:
                            previews[field_key] = PreviewArtifact(
                                field_key=field_key,
                                artifact_type="unknown",
                                files=[],
                                notes=field.preview_hint,
                            )
            continue

        canonical_map = _KEY_LOOKUP.get(logical_section, {})
        logical_section_data = section_data.setdefault(logical_section, {})
        for field in section.fields:
            normalized_label = _normalize(field.label)
            canonical_key = canonical_map.get(normalized_label)
            if canonical_key:
                logical_section_data[canonical_key] = field.value or ""
                if field.preview_present and canonical_key not in previews:
                    previews[canonical_key] = PreviewArtifact(
                        field_key=canonical_key,
                        artifact_type="unknown",
                        files=[],
                        notes=field.preview_hint,
                    )
            else:
                target = unmapped_sections.setdefault(section.section_title_raw, {})
                if field.label:
                    target[field.label] = field.value or ""
                    # Capture preview placeholders for unmapped fields
                    if field.preview_present:
                        field_key = _normalize(field.label)
                        if field_key not in previews:
                            previews[field_key] = PreviewArtifact(
                                field_key=field_key,
                                artifact_type="unknown",
                                files=[],
                                notes=field.preview_hint,
                            )

    metadata = V1Metadata(
        state_code=state_code,
        source_url=raw.source_url,
        scraped_at=raw.scraped_at,
    )

    project_section = section_data.get("project_details", {})
    project_details = V1ProjectDetails(
        registration_number=raw.registration_number or project_section.get("registration_number"),
        project_name=raw.project_name or project_section.get("project_name"),
        project_type=project_section.get("project_type"),
        project_status=project_section.get("project_status"),
        district=project_section.get("district"),
        tehsil=project_section.get("tehsil"),
        project_address=project_section.get("project_address"),
        total_units=_to_int(project_section.get("total_units")),
        total_area_sq_m=_to_float(project_section.get("total_area_sq_m")),
        launch_date=project_section.get("launch_date"),
        expected_completion_date=project_section.get("expected_completion_date"),
    )

    promoter_details = []
    promoter_section = section_data.get("promoter_details")
    if promoter_section:
        promoter_details.append(
            V1PromoterDetails(
                name=promoter_section.get("promoter_name"),
                organisation_type=promoter_section.get("promoter_type"),
                address=promoter_section.get("promoter_address"),
                email=promoter_section.get("promoter_email"),
                phone=promoter_section.get("promoter_phone"),
                pan=promoter_section.get("promoter_pan"),
                cin=promoter_section.get("promoter_cin"),
            )
        )

    land_details = []
    land_section = section_data.get("land_details")
    if land_section:
        land_details.append(
            V1LandDetails(
                land_area_sq_m=_to_float(land_section.get("land_area_sq_m")),
                land_status=land_section.get("land_status"),
                land_address=land_section.get("land_address"),
                khasra_numbers=land_section.get("khasra_numbers"),
            )
        )

    building_details = []
    building_section = section_data.get("building_details")
    if building_section:
        building_details.append(
            V1BuildingDetails(
                name=building_section.get("building_name"),
                number_of_floors=_to_int(building_section.get("number_of_floors")),
                number_of_units=_to_int(building_section.get("number_of_units")),
                carpet_area_sq_m=_to_float(building_section.get("carpet_area_sq_m")),
            )
        )

    unit_types = []
    unit_section = section_data.get("unit_types")
    if unit_section:
        unit_types.append(
            V1UnitType(
                name=unit_section.get("unit_type_name"),
                carpet_area_sq_m=_to_float(unit_section.get("unit_carpet_area_sq_m")),
                built_up_area_sq_m=_to_float(unit_section.get("unit_built_up_area_sq_m")),
                price_in_inr=_to_float(unit_section.get("unit_price_in_inr")),
            )
        )

    bank_details = []
    bank_section = section_data.get("bank_details")
    if bank_section:
        bank_details.append(
            V1BankDetails(
                bank_name=bank_section.get("bank_name"),
                branch_name=bank_section.get("branch_name"),
                account_number=bank_section.get("account_number"),
                ifsc_code=bank_section.get("ifsc_code"),
            )
        )

    documents = []
    document_section = section_data.get("documents")
    if document_section:
        documents.append(
            V1Document(
                name=document_section.get("document_name"),
                document_type=document_section.get("document_type"),
                url=document_section.get("document_url"),
                uploaded_on=document_section.get("document_uploaded_on"),
            )
        )

    quarterly_updates = []
    update_section = section_data.get("quarterly_updates")
    if update_section:
        quarterly_updates.append(
            V1QuarterlyUpdate(
                quarter=update_section.get("quarter"),
                year=update_section.get("year"),
                status=update_section.get("status"),
                completion_percent=_to_float(update_section.get("completion_percent")),
                remarks=update_section.get("remarks"),
            )
        )

    raw_data = V1RawData(sections=section_data, unmapped_sections=unmapped_sections)

    return V1Project(
        metadata=metadata,
        project_details=project_details,
        promoter_details=promoter_details,
        land_details=land_details,
        building_details=building_details,
        unit_types=unit_types,
        bank_details=bank_details,
        documents=documents,
        quarterly_updates=quarterly_updates,
        raw_data=raw_data,
        previews=previews,
    )


__all__ = ["map_raw_to_v1"]
