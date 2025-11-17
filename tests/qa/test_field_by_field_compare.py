from pathlib import Path

from cg_rera_extractor.parsing.schema import V1Project
from cg_rera_extractor.qa.field_by_field_compare import FIELD_MAPPING, compare_v1_to_html_fields
from cg_rera_extractor.qa.field_extractor import extract_label_value_map


def test_compare_v1_to_html_fields_classifies_statuses():
    html = Path("tests/qa/fixtures/detail_page.html").read_text(encoding="utf-8")
    html_fields = extract_label_value_map(html)
    v1_json = Path("tests/qa/fixtures/project_v1.json").read_text(encoding="utf-8")
    v1_project = V1Project.model_validate_json(v1_json)

    diffs = compare_v1_to_html_fields(v1_project, html_fields)

    status_map = {d["field_key"]: d["status"] for d in diffs}

    assert status_map["project_details.registration_number"] == "match"
    assert status_map["project_details.tehsil"] == "mismatch"
    assert status_map["project_details.project_status"] == "preview_unchecked"
    assert status_map["project_details.launch_date"] == "missing_in_json"
    assert status_map["project_details.expected_completion_date"] == "missing_in_html"

    # Ensure mapping stays extendable
    assert set(FIELD_MAPPING.keys()) >= {"project_details.registration_number", "project_details.project_name"}
