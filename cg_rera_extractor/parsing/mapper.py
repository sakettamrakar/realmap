"""Utilities for mapping raw extracted data to the V1 scraper schema."""
from __future__ import annotations

import json
import re
from datetime import datetime
from importlib import resources
from typing import Dict, List, Tuple

from .schema import (
    GridRecord,
    PreviewArtifact,
    RawExtractedProject,
    TableRecord,
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
_BRACKETED_TEXT_RE = re.compile(r"[\[\(].*?[\]\)]")


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    # Strip bracketed/parenthetical metadata so headings like
    # "Project Details [ Registration No : ... ]" normalize correctly.
    cleaned = _BRACKETED_TEXT_RE.sub(" ", value)
    return re.sub(r"[^a-z0-9]", "", cleaned.lower())


def _load_logical_section_mapping() -> Tuple[Dict[str, str], Dict[str, Dict[str, str]], Dict[str, Dict[str, List[str]]]]:
    resource = resources.files("cg_rera_extractor.parsing.data").joinpath(
        _LOGICAL_SECTIONS_RESOURCE
    )
    data = json.loads(resource.read_text("utf-8"))

    title_lookup: Dict[str, str] = {}
    key_lookup: Dict[str, Dict[str, str]] = {}
    table_lookup: Dict[str, Dict[str, List[str]]] = {}
    for section in data.get("sections", []):
        logical_name = section["logical_section"]
        section_titles = section.get("section_title_variants", [])
        for title in section_titles:
            title_lookup[_normalize(title)] = logical_name
        
        canonical_map: Dict[str, str] = {}
        table_map: Dict[str, List[str]] = {}
        for canonical_key, variants in section.get("keys", {}).items():
            table_map[canonical_key] = variants
            for variant in variants:
                canonical_map[_normalize(variant)] = canonical_key
        
        key_lookup[logical_name] = canonical_map
        table_lookup[logical_name] = table_map

    return title_lookup, key_lookup, table_lookup


_SECTION_LOOKUP, _KEY_LOOKUP, _TABLE_LOOKUP = _load_logical_section_mapping()

_MODEL_MAP = {
    "promoter_details": V1PromoterDetails,
    "land_details": V1LandDetails,
    "building_details": V1BuildingDetails,
    "unit_types": V1UnitType,
    "bank_details": V1BankDetails,
    "quarterly_updates": V1QuarterlyUpdate,
}


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


def _normalize_date(value: str | None) -> str | None:
    """Normalize date strings to ISO format (YYYY-MM-DD).
    
    Handles common Indian date formats and extracts dates from strings.
    """
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    
    # Try to extract something that looks like a date first
    # Matches DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, etc.
    date_match = re.search(r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})|(\d{4}-\d{2}-\d{2})', value)
    if date_match:
        value = date_match.group(0)

    # Try multiple date formats
    date_formats = (
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%Y/%m/%d",
        "%m/%d/%Y", # Fallback for some US-style dates if any
    )
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(value, fmt)
            # Handle 2-digit years
            if dt.year < 100:
                if dt.year > 50:
                    dt = dt.replace(year=1900 + dt.year)
                else:
                    dt = dt.replace(year=2000 + dt.year)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # Return None if no format matched
    return None


def _map_table_to_model(table: TableRecord, model_class: type, mapping: Dict[str, str]) -> List[any]:
    """Map a TableRecord to a list of Pydantic models based on header mapping."""
    results = []
    headers = [h.lower() for h in table.headers]
    
    # Create index map: canonical_key -> column_index
    col_map = {}
    for canonical_key, variants in mapping.items():
        for variant in variants:
            variant_norm = variant.lower()
            for idx, h in enumerate(headers):
                if variant_norm in h:
                    col_map[canonical_key] = idx
                    break
            if canonical_key in col_map:
                break
                
    if not col_map:
        return []
        
    for row in table.rows:
        if not row:
            continue
            
        data = {}
        for key, idx in col_map.items():
            if idx < len(row):
                val = row[idx]
                # Basic type conversion based on field name heuristics
                if any(k in key for k in ["area", "price", "percent", "amount"]):
                    data[key] = _to_float(val)
                elif any(k in key for k in ["number", "units", "floors", "year"]):
                    data[key] = _to_int(val)
                elif "date" in key:
                    data[key] = _normalize_date(val)
                else:
                    data[key] = val
        
        try:
            results.append(model_class(**data))
        except Exception:
            # Skip rows that fail validation
            continue
            
    return results


def _extract_pincode(address: str | None) -> str | None:
    """Extract 6-digit Indian pincode from address string."""
    if not address:
        return None
    # Look for 6-digit number that could be a pincode
    match = re.search(r'\b(\d{6})\b', address)
    return match.group(1) if match else None


def _infer_doc_type(field_key: str) -> str:
    """Infer document type from field key."""
    key_lower = field_key.lower()
    
    doc_type_mapping = {
        'registration': 'registration_certificate',
        'building': 'building_plan',
        'layout': 'layout_plan',
        'fire': 'fire_noc',
        'environment': 'environment_noc',
        'airport': 'airport_noc',
        'encumbrance': 'encumbrance_certificate',
        'commencement': 'commencement_certificate',
        'occupancy': 'occupancy_certificate',
        'completion': 'completion_certificate',
        'revenue': 'revenue_document',
        'title': 'land_title_deed',
        'brochure': 'project_brochure',
        'photo': 'site_photo',
    }
    
    for keyword, doc_type in doc_type_mapping.items():
        if keyword in key_lower:
            return doc_type
    
    return 'unknown'


def map_raw_to_v1(raw: RawExtractedProject, state_code: str = "CG") -> V1Project:
    """Map a :class:`RawExtractedProject` into the V1 scraper schema."""

    section_data: Dict[str, Dict[str, str]] = {}
    unmapped_sections: Dict[str, Dict[str, str]] = {}
    raw_tables: Dict[str, List[TableRecord]] = {}
    raw_grids: Dict[str, List[GridRecord]] = {}
    previews: Dict[str, PreviewArtifact] = {}
    extracted_documents: List[V1Document] = []
    
    # Lists to hold multiple records from tables
    promoter_details: List[V1PromoterDetails] = []
    land_details: List[V1LandDetails] = []
    building_details: List[V1BuildingDetails] = []
    unit_types: List[V1UnitType] = []
    bank_details: List[V1BankDetails] = []
    quarterly_updates: List[V1QuarterlyUpdate] = []

    for section in raw.sections:
        if section.tables:
            raw_tables[section.section_title_raw] = section.tables
        if section.grids:
            raw_grids[section.section_title_raw] = section.grids
            
        normalized_title = _normalize(section.section_title_raw)
        logical_section = _SECTION_LOOKUP.get(normalized_title)
        
        # Process tables for known logical sections
        if logical_section in _MODEL_MAP:
            model_class = _MODEL_MAP[logical_section]
            table_mapping = _TABLE_LOOKUP.get(logical_section, {})
            for table in section.tables:
                records = _map_table_to_model(table, model_class, table_mapping)
                if logical_section == "promoter_details": promoter_details.extend(records)
                elif logical_section == "land_details": land_details.extend(records)
                elif logical_section == "building_details": building_details.extend(records)
                elif logical_section == "unit_types": unit_types.extend(records)
                elif logical_section == "bank_details": bank_details.extend(records)
                elif logical_section == "quarterly_updates": quarterly_updates.extend(records)

        if logical_section == "documents":
            canonical_map = _KEY_LOOKUP.get(logical_section, {})
            logical_section_data = section_data.setdefault(logical_section, {})
            
            for field in section.fields:
                if not field.label:
                    continue

                normalized_label = _normalize(field.label)
                canonical_key = canonical_map.get(normalized_label)

                if canonical_key:
                    logical_section_data[canonical_key] = field.value or ""
                else:
                    # Implicit document: Label is name, Value is URL
                    doc_url = "NA"
                    if field.links:
                        doc_url = field.links[0]
                    elif field.preview_hint and not field.preview_hint.startswith(("#", ".")):
                        doc_url = field.preview_hint
                    elif field.value and field.value not in ("Preview", "Download", "View"):
                        doc_url = field.value
                    
                    extracted_documents.append(
                        V1Document(
                            name=field.label,
                            document_type="Unknown",
                            url=doc_url,
                            uploaded_on=None,
                        )
                    )

                if field.preview_present:
                    key_for_preview = canonical_key if canonical_key else normalized_label
                    if key_for_preview not in previews:
                        previews[key_for_preview] = PreviewArtifact(
                            field_key=key_for_preview,
                            artifact_type="unknown",
                            files=[],
                            notes=field.preview_hint,
                        )
            continue

        if not logical_section:
            target = unmapped_sections.setdefault(section.section_title_raw, {})
            for field in section.fields:
                if field.label:
                    target[field.label] = field.value or ""
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

    # --- Project Details ---
    project_section = section_data.get("project_details", {})
    project_address = project_section.get("project_address")
    pincode = project_section.get("pincode") or _extract_pincode(project_address)
    village_or_locality = project_section.get("village_or_locality")
    project_website_url = project_section.get("project_website")
    
    project_details = V1ProjectDetails(
        registration_number=raw.registration_number or project_section.get("registration_number"),
        project_name=raw.project_name or project_section.get("project_name"),
        project_type=project_section.get("project_type"),
        project_status=project_section.get("project_status"),
        district=project_section.get("district"),
        tehsil=project_section.get("tehsil"),
        village_or_locality=village_or_locality,
        pincode=pincode,
        project_address=project_address,
        project_website_url=project_website_url,
        total_units=_to_int(project_section.get("total_units")),
        total_area_sq_m=_to_float(project_section.get("total_area_sq_m")),
        launch_date=_normalize_date(project_section.get("launch_date")),
        expected_completion_date=_normalize_date(project_section.get("expected_completion_date")),
    )
    project_details._extra = {
        "pincode": pincode,
        "village_or_locality": village_or_locality,
        "project_website_url": project_website_url,
    }

    # --- Merge Field-based data with Table-based data ---
    def _merge_fields(logical_name, current_list, model_class):
        fields = section_data.get(logical_name)
        if fields:
            try:
                # Convert types for fields
                typed_fields = {}
                for k, v in fields.items():
                    if any(x in k for x in ["area", "price", "percent", "amount"]):
                        typed_fields[k] = _to_float(v)
                    elif any(x in k for x in ["number", "units", "floors", "year"]):
                        typed_fields[k] = _to_int(v)
                    elif "date" in k:
                        typed_fields[k] = _normalize_date(v)
                    else:
                        typed_fields[k] = v
                
                obj = model_class(**typed_fields)
                # Only add if it has some meaningful data and not already present
                if any(getattr(obj, f) for f in obj.model_fields if getattr(obj, f)):
                    current_list.insert(0, obj)
            except Exception:
                pass
        return current_list

    promoter_details = _merge_fields("promoter_details", promoter_details, V1PromoterDetails)
    land_details = _merge_fields("land_details", land_details, V1LandDetails)
    building_details = _merge_fields("building_details", building_details, V1BuildingDetails)
    unit_types = _merge_fields("unit_types", unit_types, V1UnitType)
    bank_details = _merge_fields("bank_details", bank_details, V1BankDetails)
    quarterly_updates = _merge_fields("quarterly_updates", quarterly_updates, V1QuarterlyUpdate)

    # --- Documents ---
    documents = list(extracted_documents)
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

    raw_data = V1RawData(
        sections=section_data, 
        unmapped_sections=unmapped_sections,
        tables=raw_tables,
        grids=raw_grids
    )

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
