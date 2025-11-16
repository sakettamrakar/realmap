"""Helpers for persisting raw project detail HTML files."""

from __future__ import annotations

from pathlib import Path
import re


_NON_WORD_RE = re.compile(r"[^A-Za-z0-9]+")


def _sanitize_reg_no(reg_no: str) -> str:
    cleaned = _NON_WORD_RE.sub("_", reg_no.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "unknown"


def make_project_html_path(output_base: str, reg_no: str) -> str:
    """Return a deterministic path for storing the project's detail HTML."""

    sanitized = _sanitize_reg_no(reg_no)
    raw_dir = Path(output_base) / "raw_html"
    filename = f"project_{sanitized}.html"
    return str(raw_dir / filename)


def save_project_html(path: str, html: str) -> None:
    """Ensure the parent directory exists and persist the HTML as UTF-8."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")

