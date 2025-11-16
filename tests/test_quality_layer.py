from __future__ import annotations

from cg_rera_extractor.parsing.schema import (
    V1LandDetails,
    V1Metadata,
    V1Project,
    V1ProjectDetails,
    V1RawData,
)
from cg_rera_extractor.quality import (
    clean_reg_no,
    normalize_district,
    normalize_project_type,
    normalize_status,
    normalize_v1_project,
    validate_v1_project,
)


def _base_project(**project_kwargs) -> V1Project:
    return V1Project(
        metadata=V1Metadata(state_code="CG"),
        project_details=V1ProjectDetails(**project_kwargs),
        raw_data=V1RawData(),
    )


def test_normalization_helpers_basic_cases():
    assert normalize_district(" raipur") == "Raipur"
    assert normalize_district("BILASPUR") == "Bilaspur"
    assert normalize_status("on-going ") == "Ongoing"
    assert normalize_project_type("residential & commercial") == "Residential and Commercial"
    assert clean_reg_no(" cg - reg - 001 ") == "CG-REG-001"


def test_normalize_v1_project_applies_field_normalization():
    project = _base_project(
        registration_number=" cg / reg / 002 ",
        project_status="ongoing",
        project_type="mixed-use",
        district="  rAipur ",
        project_name="   demo  project  ",
        project_address=" 123  main road   raipur ",
    )

    normalized = normalize_v1_project(project)

    details = normalized.project_details
    assert details.registration_number == "CG/REG/002"
    assert details.project_status == "Ongoing"
    assert details.project_type == "Mixed Use"
    assert details.district == "Raipur"
    assert details.project_name == "demo project"
    assert details.project_address == "123 main road raipur"


def test_validation_flags_missing_fields_and_bad_values():
    project = _base_project(project_status=None)

    messages = validate_v1_project(project)

    assert any("district" in msg for msg in messages)
    assert any("status" in msg for msg in messages)


def test_validation_catches_pincode_and_land_area():
    project = V1Project(
        metadata=V1Metadata(state_code="CG"),
        project_details=V1ProjectDetails(district="Raipur", project_status="Registered"),
        land_details=[V1LandDetails(land_area_sq_m=-10)],
        raw_data=V1RawData(sections={"project_details": {"pincode": "4900"}}),
    )

    messages = validate_v1_project(project)

    assert any("pincode" in msg.lower() for msg in messages)
    assert any("land_area_sq_m" in msg for msg in messages)
