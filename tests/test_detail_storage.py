"""Tests for detail HTML storage helpers."""

from cg_rera_extractor.detail.storage import (
    make_project_html_path,
    make_project_key,
    save_project_html,
)


def test_make_project_html_path_sanitizes_reg_no(tmp_path):
    project_key = make_project_key("CG", "CG/123 45-A")
    path = make_project_html_path(str(tmp_path), project_key)
    expected = tmp_path / "raw_html" / "project_CG_CG_123_45_A.html"
    assert path == str(expected)


def test_save_project_html_creates_directory(tmp_path):
    target = tmp_path / "raw_html" / "project_test.html"
    html = "<html><body>content</body></html>"
    save_project_html(str(target), html)
    assert target.exists()
    assert target.read_text(encoding="utf-8") == html

