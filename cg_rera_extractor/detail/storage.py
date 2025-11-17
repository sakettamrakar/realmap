"""Helpers for persisting raw project detail HTML files."""

from __future__ import annotations

from pathlib import Path
import re


_NON_WORD_RE = re.compile(r"[^A-Za-z0-9]+")


def make_project_key(state_code: str, reg_no: str) -> str:
    """Build a stable project key for artifacts using state and registration."""

    cleaned_reg_no = _sanitize_reg_no(reg_no)
    return f"{state_code}_{cleaned_reg_no}" if state_code else cleaned_reg_no


def _sanitize_reg_no(reg_no: str) -> str:
    cleaned = _NON_WORD_RE.sub("_", reg_no.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "unknown"


def make_project_html_path(output_base: str, project_key: str) -> str:
    """Return a deterministic path for storing the project's detail HTML."""

    sanitized = _sanitize_reg_no(project_key)
    raw_dir = Path(output_base) / "raw_html"
    filename = f"project_{sanitized}.html"
    return str(raw_dir / filename)


def make_preview_dir(output_base: str, project_key: str, field_key: str | None = None) -> Path:
    """Return the directory where preview artifacts for a field should live."""

    base = Path(output_base) / "previews" / _sanitize_reg_no(project_key)
    if field_key:
        base = base / _sanitize_reg_no(field_key)
    return base


def save_project_html(path: str, html: str) -> None:
    """Ensure the parent directory exists and persist the HTML as UTF-8."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")

