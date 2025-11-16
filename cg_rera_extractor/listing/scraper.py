"""Utilities to parse CG RERA listing HTML."""

from __future__ import annotations

from typing import Iterable
from urllib.parse import urljoin
import re

from bs4 import BeautifulSoup

from .models import ListingRecord


_HEADER_ALIASES: dict[str, set[str]] = {
    "reg_no": {
        "reg no",
        "registration no",
        "registration number",
        "reg number",
    },
    "project_name": {"project name", "project"},
    "promoter_name": {"promoter name", "promoter"},
    "district": {"district"},
    "tehsil": {"tehsil", "tahsil"},
    "status": {"status"},
    "detail_url": {"details", "detail", "view", "view details"},
}


def _normalize_header(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return " ".join(normalized.split())


def _match_headers(headers: Iterable[str]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for idx, header in enumerate(headers):
        normalized = _normalize_header(header)
        for field, aliases in _HEADER_ALIASES.items():
            if normalized in aliases and field not in mapping:
                mapping[field] = idx
    return mapping


def _get_cell_text(cells, index: int | None) -> str | None:
    if index is None or index >= len(cells):
        return None
    text = cells[index].get_text(" ", strip=True)
    return text or None


def _extract_detail_url(cells, index: int | None, base_url: str) -> str | None:
    candidates = []
    if index is not None and index < len(cells):
        candidates.append(cells[index])
    if not candidates:
        candidates = cells
    for cell in candidates:
        link = cell.find("a")
        if link and link.get("href"):
            return urljoin(base_url, link["href"].strip())
    return None


def parse_listing_html(html: str, base_url: str) -> list[ListingRecord]:
    """Parse a CG RERA listing search HTML page into ListingRecord entries."""

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return []

    target_table = None
    best_score = -1
    for table in tables:
        headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
        if not headers:
            continue
        header_map = _match_headers(headers)
        score = len(header_map)
        if score > best_score:
            best_score = score
            target_table = (table, header_map)

    if target_table is None:
        return []

    table, header_map = target_table
    records: list[ListingRecord] = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        reg_no = _get_cell_text(cells, header_map.get("reg_no"))
        project_name = _get_cell_text(cells, header_map.get("project_name"))
        detail_url = _extract_detail_url(cells, header_map.get("detail_url"), base_url)
        if not (reg_no and project_name and detail_url):
            continue
        record = ListingRecord(
            reg_no=reg_no,
            project_name=project_name,
            promoter_name=_get_cell_text(cells, header_map.get("promoter_name")),
            district=_get_cell_text(cells, header_map.get("district")),
            tehsil=_get_cell_text(cells, header_map.get("tehsil")),
            status=_get_cell_text(cells, header_map.get("status")),
            detail_url=detail_url,
        )
        records.append(record)
    return records
