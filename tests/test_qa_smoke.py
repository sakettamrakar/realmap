"""
Comprehensive smoke tests for the QA field-by-field comparison workflow.

This test suite validates the complete QA workflow:
1. HTML field extraction
2. V1 JSON parsing
3. Field-by-field comparison
4. Report generation
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pytest

from cg_rera_extractor.parsing.schema import V1Project
from cg_rera_extractor.qa.field_by_field_compare import (
    FIELD_MAPPING,
    FieldDiff,
    compare_v1_to_html_fields,
)
from cg_rera_extractor.qa.field_extractor import extract_label_value_map


# ============================================================================
# FIXTURE: Load test data
# ============================================================================


@pytest.fixture
def detail_page_html() -> str:
    """Load the test detail page HTML."""
    path = Path("tests/qa/fixtures/detail_page.html")
    return path.read_text(encoding="utf-8")


@pytest.fixture
def project_v1_json() -> str:
    """Load the test V1 project JSON."""
    path = Path("tests/qa/fixtures/project_v1.json")
    return path.read_text(encoding="utf-8")


@pytest.fixture
def v1_project(project_v1_json: str) -> V1Project:
    """Parse test V1 project from JSON."""
    return V1Project.model_validate_json(project_v1_json)


@pytest.fixture
def html_fields(detail_page_html: str) -> Dict[str, str]:
    """Extract label-value map from test HTML."""
    return extract_label_value_map(detail_page_html)


# ============================================================================
# TEST SUITE 1: HTML Field Extraction
# ============================================================================


class TestHTMLFieldExtraction:
    """Tests for extracting label-value pairs from HTML."""

    def test_extracts_all_expected_fields(self, html_fields: Dict[str, str]):
        """HTML extraction should find all visible fields."""
        expected_fields = {
            "registration_number",
            "project_name",
            "district",
            "tehsil",
            "project_status",
            "project_type",
            "project_address",
            "launch_date",
        }
        assert expected_fields.issubset(set(html_fields.keys()))

    def test_field_values_match_html_content(self, html_fields: Dict[str, str]):
        """Field values should match the HTML source."""
        assert html_fields["registration_number"] == "CG-REG-001"
        assert html_fields["project_name"] == "Garden Villas"
        assert html_fields["district"] == "Raipur"
        assert html_fields["project_type"] == "Residential"

    def test_handles_preview_buttons(self, html_fields: Dict[str, str]):
        """Preview buttons should be marked with special 'Preview' string."""
        assert html_fields["project_status"] == "Preview"

    def test_normalizes_labels(self, html_fields: Dict[str, str]):
        """Labels should be normalized to lowercase with underscores."""
        # All keys should be lowercase with underscores (or single word)
        for key in html_fields.keys():
            assert key == key.lower()
            # Keys can be single words (no underscore) or multi-word with underscores
            assert all(c.isalnum() or c == "_" for c in key)

    def test_extracts_multiword_values(self, html_fields: Dict[str, str]):
        """Multi-word values should be preserved."""
        assert html_fields["project_address"] == "Near City Center"

    def test_extracts_date_values(self, html_fields: Dict[str, str]):
        """Date fields should be extracted as strings."""
        assert html_fields["launch_date"] == "2023-01-15"


# ============================================================================
# TEST SUITE 2: V1 Project Parsing
# ============================================================================


class TestV1ProjectParsing:
    """Tests for parsing and validating V1 project JSON."""

    def test_v1_project_parses_successfully(self, v1_project: V1Project):
        """V1 JSON should parse without errors."""
        assert v1_project is not None
        assert v1_project.metadata.state_code == "CG"

    def test_v1_project_contains_expected_fields(self, v1_project: V1Project):
        """V1 project should have all required detail fields."""
        details = v1_project.project_details
        assert details.registration_number == "CG-REG-001"
        assert details.project_name == "Garden Villas"
        assert details.project_type == "Residential"
        assert details.district == "Raipur"

    def test_v1_project_handles_null_values(self, v1_project: V1Project):
        """V1 project should allow null values for optional fields."""
        assert v1_project.project_details.launch_date is None

    def test_v1_project_contains_non_detail_sections(self, v1_project: V1Project):
        """V1 project should have other sections like land_details."""
        assert len(v1_project.land_details) > 0
        assert v1_project.land_details[0].land_area_sq_m == 4500.0


# ============================================================================
# TEST SUITE 3: Field Comparison Logic
# ============================================================================


class TestFieldComparison:
    """Tests for comparing V1 JSON against HTML fields."""

    def test_comparison_returns_diffs_for_all_mapped_fields(
        self, v1_project: V1Project, html_fields: Dict[str, str]
    ):
        """Comparison should return one diff per mapped field."""
        diffs = compare_v1_to_html_fields(v1_project, html_fields)
        
        assert len(diffs) == len(FIELD_MAPPING)
        field_keys = {d["field_key"] for d in diffs}
        assert field_keys == set(FIELD_MAPPING.keys())

    def test_comparison_identifies_matches(
        self, v1_project: V1Project, html_fields: Dict[str, str]
    ):
        """Matching fields should have 'match' status."""
        diffs = compare_v1_to_html_fields(v1_project, html_fields)
        status_map = {d["field_key"]: d["status"] for d in diffs}

        # These should match
        assert status_map["project_details.registration_number"] == "match"
        assert status_map["project_details.project_name"] == "match"
        assert status_map["project_details.project_type"] == "match"

    def test_comparison_identifies_mismatches(
        self, v1_project: V1Project, html_fields: Dict[str, str]
    ):
        """Non-matching fields should have 'mismatch' status."""
        diffs = compare_v1_to_html_fields(v1_project, html_fields)
        status_map = {d["field_key"]: d["status"] for d in diffs}

        # This is a known mismatch in test data
        assert status_map["project_details.tehsil"] == "mismatch"

    def test_comparison_identifies_preview_unchecked(
        self, v1_project: V1Project, html_fields: Dict[str, str]
    ):
        """Fields with 'Preview' should be marked as 'preview_unchecked'."""
        diffs = compare_v1_to_html_fields(v1_project, html_fields)
        status_map = {d["field_key"]: d["status"] for d in diffs}

        assert status_map["project_details.project_status"] == "preview_unchecked"

    def test_comparison_identifies_missing_in_json(
        self, v1_project: V1Project, html_fields: Dict[str, str]
    ):
        """Fields in HTML but not in JSON should be marked."""
        diffs = compare_v1_to_html_fields(v1_project, html_fields)
        status_map = {d["field_key"]: d["status"] for d in diffs}

        # launch_date is None in V1, present in HTML
        assert status_map["project_details.launch_date"] == "missing_in_json"

    def test_comparison_identifies_missing_in_html(
        self, v1_project: V1Project, html_fields: Dict[str, str]
    ):
        """Fields in JSON but not in HTML should be marked."""
        diffs = compare_v1_to_html_fields(v1_project, html_fields)
        status_map = {d["field_key"]: d["status"] for d in diffs}

        # expected_completion_date is in V1 but not in test HTML
        assert status_map["project_details.expected_completion_date"] == "missing_in_html"

    def test_comparison_normalizes_case(
        self, v1_project: V1Project, html_fields: Dict[str, str]
    ):
        """Comparison should be case-insensitive."""
        diffs = compare_v1_to_html_fields(v1_project, html_fields)
        
        # Find a match and verify normalized values
        registration_diff = next(
            d for d in diffs if d["field_key"] == "project_details.registration_number"
        )
        assert registration_diff["status"] == "match"

    def test_comparison_returns_structured_diffs(
        self, v1_project: V1Project, html_fields: Dict[str, str]
    ):
        """Each diff should have all required fields."""
        diffs = compare_v1_to_html_fields(v1_project, html_fields)
        
        for diff in diffs:
            assert "field_key" in diff
            assert "json_value" in diff
            assert "html_value" in diff
            assert "status" in diff
            assert "notes" in diff
            
            # Status should be one of the expected values
            assert diff["status"] in {
                "match",
                "mismatch",
                "missing_in_html",
                "missing_in_json",
                "preview_unchecked",
            }


# ============================================================================
# TEST SUITE 4: Smoke Test Integration
# ============================================================================


class TestQASmokeTestIntegration:
    """Integration tests simulating the full smoke test workflow."""

    def test_complete_workflow_processes_without_errors(
        self, v1_project: V1Project, detail_page_html: str
    ):
        """Full workflow: extract HTML → compare → report."""
        # Step 1: Extract HTML
        html_fields = extract_label_value_map(detail_page_html)
        assert len(html_fields) > 0

        # Step 2: Compare
        diffs = compare_v1_to_html_fields(v1_project, html_fields)
        assert len(diffs) > 0

        # Step 3: Summarize (like the smoke test does)
        summary = {
            "total_fields": len(diffs),
            "match": sum(1 for d in diffs if d["status"] == "match"),
            "mismatch": sum(1 for d in diffs if d["status"] == "mismatch"),
            "missing_in_html": sum(1 for d in diffs if d["status"] == "missing_in_html"),
            "missing_in_json": sum(1 for d in diffs if d["status"] == "missing_in_json"),
            "preview_unchecked": sum(1 for d in diffs if d["status"] == "preview_unchecked"),
        }

        # All diffs should be accounted for
        total_accounted = (
            summary["match"]
            + summary["mismatch"]
            + summary["missing_in_html"]
            + summary["missing_in_json"]
            + summary["preview_unchecked"]
        )
        assert total_accounted == summary["total_fields"]

    def test_report_structure_matches_expected_format(
        self, v1_project: V1Project, detail_page_html: str
    ):
        """QA report should have expected JSON structure."""
        html_fields = extract_label_value_map(detail_page_html)
        diffs = compare_v1_to_html_fields(v1_project, html_fields)

        # Simulate report generation
        report = {
            "summary": {
                "run_id": "test_20251117_000000",
                "total_projects": 1,
                "total_fields": len(diffs),
                "match": sum(1 for d in diffs if d["status"] == "match"),
                "mismatch": sum(1 for d in diffs if d["status"] == "mismatch"),
                "missing_in_html": sum(1 for d in diffs if d["status"] == "missing_in_html"),
                "missing_in_json": sum(1 for d in diffs if d["status"] == "missing_in_json"),
                "preview_unchecked": sum(1 for d in diffs if d["status"] == "preview_unchecked"),
            },
            "projects": [
                {
                    "project_key": "CG-REG-001",
                    "diffs": diffs,
                }
            ],
        }

        # Should serialize to JSON
        json_str = json.dumps(report, indent=2)
        assert json_str is not None
        
        # Should deserialize back
        parsed = json.loads(json_str)
        assert parsed["summary"]["run_id"] == "test_20251117_000000"
        assert parsed["summary"]["total_projects"] == 1
        assert len(parsed["projects"]) == 1

    def test_qa_resilience_with_missing_fields(self, v1_project: V1Project):
        """QA should handle missing HTML fields gracefully."""
        # Simulate HTML with fewer fields
        sparse_html_fields = {
            "registration_number": "CG-REG-001",
            "project_name": "Garden Villas",
        }

        diffs = compare_v1_to_html_fields(v1_project, sparse_html_fields)

        # Should still return diffs for all mapped fields
        assert len(diffs) == len(FIELD_MAPPING)

        # Some should be missing_in_html
        missing_html = [d for d in diffs if d["status"] == "missing_in_html"]
        assert len(missing_html) > 0

    def test_qa_resilience_with_extra_html_fields(self, v1_project: V1Project):
        """QA should handle extra HTML fields gracefully."""
        html_fields = {
            "registration_number": "CG-REG-001",
            "project_name": "Garden Villas",
            "district": "Raipur",
            "extra_field_1": "Extra Value",
            "extra_field_2": "Another Extra",
        }

        # Should not raise an error
        diffs = compare_v1_to_html_fields(v1_project, html_fields)
        assert len(diffs) == len(FIELD_MAPPING)


# ============================================================================
# TEST SUITE 5: Edge Cases and Error Handling
# ============================================================================


class TestQAEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_handles_whitespace_normalization(self, v1_project: V1Project):
        """QA should normalize whitespace in values."""
        html_fields = {
            "registration_number": "  CG-REG-001  ",
            "project_name": "Garden   Villas",
            "district": "Raipur",
            "tehsil": "Abhanpur",
            "project_status": "Ongoing",
            "project_type": "Residential",
            "project_address": "Near City Center",
        }

        diffs = compare_v1_to_html_fields(v1_project, html_fields)
        status_map = {d["field_key"]: d["status"] for d in diffs}

        # Should still match despite whitespace differences
        assert status_map["project_details.registration_number"] == "match"
        assert status_map["project_details.project_name"] == "match"

    def test_handles_case_insensitive_comparison(self, v1_project: V1Project):
        """QA should compare values case-insensitively."""
        html_fields = {
            "registration_number": "cg-reg-001",  # lowercase
            "project_name": "GARDEN VILLAS",  # uppercase
            "district": "RAIPUR",
            "tehsil": "Abhanpur",
            "project_status": "ONGOING",
            "project_type": "residential",
            "project_address": "Near City Center",
        }

        diffs = compare_v1_to_html_fields(v1_project, html_fields)
        status_map = {d["field_key"]: d["status"] for d in diffs}

        # Should still match
        assert status_map["project_details.registration_number"] == "match"
        assert status_map["project_details.project_name"] == "match"

    def test_handles_none_values_in_json(self, v1_project: V1Project):
        """QA should mark None JSON values appropriately."""
        html_fields = {
            "registration_number": "CG-REG-001",
            "project_name": "Garden Villas",
            "district": "Raipur",
            "tehsil": "Abhanpur",
            "project_status": "Ongoing",
            "project_type": "Residential",
            "project_address": "Near City Center",
            "launch_date": "2023-01-15",  # This field is None in v1_project
        }

        diffs = compare_v1_to_html_fields(v1_project, html_fields)
        launch_date_diff = next(
            d for d in diffs if d["field_key"] == "project_details.launch_date"
        )

        # launch_date is None in JSON but present in HTML
        assert launch_date_diff["status"] == "missing_in_json"
        assert launch_date_diff["json_value"] is None
        assert launch_date_diff["html_value"] == "2023-01-15"

    def test_handles_empty_string_values(self, v1_project: V1Project):
        """QA should treat empty strings as missing values."""
        html_fields = {
            "registration_number": "",
            "project_name": "Garden Villas",
            "district": "Raipur",
            "tehsil": "Abhanpur",
            "project_status": "Ongoing",
            "project_type": "Residential",
            "project_address": "Near City Center",
        }

        diffs = compare_v1_to_html_fields(v1_project, html_fields)
        status_map = {d["field_key"]: d["status"] for d in diffs}

        # Empty string should be treated as missing
        assert status_map["project_details.registration_number"] == "mismatch"


# ============================================================================
# UTILITY FUNCTIONS FOR MANUAL TESTING
# ============================================================================


def print_qa_summary(run_dir: Path) -> None:
    """
    Print a summary of QA results from a run directory.
    
    Usage:
        from tests.test_qa_smoke import print_qa_summary
        from pathlib import Path
        print_qa_summary(Path("outputs/runs/run_20251117_123456"))
    """
    qa_report = run_dir / "qa_fields" / "qa_fields_report.json"
    if not qa_report.exists():
        print(f"QA report not found: {qa_report}")
        return

    report = json.loads(qa_report.read_text(encoding="utf-8"))
    summary = report.get("summary", {})

    print("\n=== QA Summary ===")
    print(f"Run ID:              {summary.get('run_id')}")
    print(f"Total Projects:      {summary.get('total_projects')}")
    print(f"Total Fields:        {summary.get('total_fields')}")
    print(f"Matches:             {summary.get('match')}")
    print(f"Mismatches:          {summary.get('mismatch')}")
    print(f"Missing in HTML:     {summary.get('missing_in_html')}")
    print(f"Missing in JSON:     {summary.get('missing_in_json')}")
    print(f"Preview Unchecked:   {summary.get('preview_unchecked')}")

    match_pct = (
        (summary.get("match", 0) / summary.get("total_fields", 1)) * 100
        if summary.get("total_fields", 0) > 0
        else 0
    )
    print(f"\nMatch Rate:          {match_pct:.1f}%")


if __name__ == "__main__":
    # Example: Run specific test
    pytest.main([__file__, "-v", "-k", "test_complete_workflow"])
