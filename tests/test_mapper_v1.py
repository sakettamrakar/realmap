"""Tests for the RawExtracted -> V1Project mapper."""
from __future__ import annotations

import json
from pathlib import Path

from cg_rera_extractor.parsing import RawExtractedProject, map_raw_to_v1

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "raw_extracted_sample.json"


def load_raw_fixture() -> RawExtractedProject:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return RawExtractedProject.model_validate(data)


def test_map_raw_to_v1_populates_project_and_promoter_details():
    raw = load_raw_fixture()
    v1 = map_raw_to_v1(raw)

    assert v1.project_details.registration_number == "CG-REG-2024-001"
    assert v1.project_details.project_name == "Emerald Residency"
    assert v1.project_details.district == "Raipur"
    assert v1.project_details.total_units == 180

    assert len(v1.promoter_details) == 1
    promoter = v1.promoter_details[0]
    assert promoter.name == "Green Estates Pvt Ltd"
    assert promoter.organisation_type == "Company"
    assert promoter.email == "contact@greenestates.in"


def test_map_raw_to_v1_preserves_unmapped_sections():
    raw = load_raw_fixture()
    v1 = map_raw_to_v1(raw)

    assert "Special Approvals" in v1.raw_data.unmapped_sections
    special = v1.raw_data.unmapped_sections["Special Approvals"]
    assert special["Airport Clearance"] == "Pending"
    assert "project_details" in v1.raw_data.sections
    assert v1.raw_data.sections["project_details"]["district"] == "Raipur"
