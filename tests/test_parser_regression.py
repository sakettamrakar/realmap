"""Tests for the parser regression harness."""

import json

from tools import parser_regression


def test_record_and_check_round_trip(tmp_path):
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    fixture = fixtures_dir / "tiny.html"
    fixture.write_text(
        """
        <html>
            <body>
                <table>
                    <tr><th>Reg No</th><th>Project Name</th><th>Details</th></tr>
                    <tr><td>CG-001</td><td>Tiny Project</td><td><a href="/details/CG-001">View</a></td></tr>
                </table>
                <h4>Project Details</h4>
                <label>Project Name:</label> Tiny Project
            </body>
        </html>
        """,
        encoding="utf-8",
    )

    golden_dir = tmp_path / "golden"
    recorded = parser_regression.record_golden([fixture], golden_dir, base_url="https://example.com/")

    assert recorded[0].exists()

    discrepancies = parser_regression.check_golden([fixture], golden_dir, base_url="https://example.com/")
    assert discrepancies == []

    payload = json.loads(recorded[0].read_text(encoding="utf-8"))
    assert payload["listing"][0]["detail_url"] == "https://example.com/details/CG-001"
    assert payload["raw"]["sections"]
    assert payload["v1"]["project_details"]["project_name"] == "Tiny Project"
