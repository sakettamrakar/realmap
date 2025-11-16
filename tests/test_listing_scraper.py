"""Tests for listing HTML parser."""

from pathlib import Path

from cg_rera_extractor.listing import parse_listing_html


def test_parse_listing_html_loads_records():
    fixture_path = Path("tests/fixtures/listing_sample.html")
    html = fixture_path.read_text(encoding="utf-8")

    records = parse_listing_html(html, base_url="https://rera.cg.gov")

    assert len(records) == 2
    first = records[0]
    assert first.reg_no == "CG-REG-123"
    assert first.project_name == "Sunshine Residency"
    assert first.promoter_name == "Sun Builders"
    assert first.district == "Raipur"
    assert first.tehsil == "Tilda"
    assert first.status == "Registered"
    assert first.detail_url == "https://rera.cg.gov/details/CG-REG-123"
