"""Utilities for working with saved MHTML pages."""
from __future__ import annotations

from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Iterable


def _iter_html_parts(mhtml_bytes: bytes) -> Iterable[str]:
    """Yield decoded HTML payloads from an MHTML document."""

    message = BytesParser(policy=policy.default).parsebytes(mhtml_bytes)
    for part in message.walk():
        if part.get_content_type() != "text/html":
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        charset = part.get_content_charset() or "utf-8"
        yield payload.decode(charset, errors="replace")


def extract_html_from_mhtml(path: str | Path) -> str:
    """Extract the first HTML document contained in an MHTML archive."""

    data = Path(path).read_bytes()
    for html in _iter_html_parts(data):
        if html.strip():
            return html
    raise ValueError(f"No HTML parts found in {path}")


__all__ = ["extract_html_from_mhtml"]
