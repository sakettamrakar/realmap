from pathlib import Path

from cg_rera_extractor.qa.field_extractor import extract_label_value_map


def test_extract_label_value_map_handles_tables_and_preview():
    html = Path("tests/qa/fixtures/detail_page.html").read_text(encoding="utf-8")

    result = extract_label_value_map(html)

    assert result["registration_number"] == "CG-REG-001"
    assert result["project_name"] == "Garden Villas"
    assert result["district"] == "Raipur"
    assert result["tehsil"] == "Tilda"
    assert result["project_status"] == "Preview"
    assert result["project_type"] == "Residential"
    assert result["project_address"] == "Near City Center"
    assert result["launch_date"] == "2023-01-15"
