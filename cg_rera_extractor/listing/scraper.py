"""Utilities to parse CG RERA listing HTML."""

from __future__ import annotations

import logging
import re
from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .models import ListingRecord

LOGGER = logging.getLogger(__name__)


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


def _extract_detail_url(
    cells, index: int | None, base_url: str, link_selector: str | None
) -> str | None:
    candidates = []
    if index is not None and index < len(cells):
        candidates.append(cells[index])
    if not candidates:
        candidates = cells

    fallback_href: str | None = None
    for cell in candidates:
        if link_selector:
            links = cell.select(link_selector)
        else:
            links = cell.find_all("a")
        for link in links:
            href = (link.get("href") or "").strip()
            text = link.get_text(" ", strip=True).lower()
            if not href:
                continue
            if link_selector is None and "detail" not in text and "view" not in text:
                if fallback_href is None:
                    fallback_href = href
                continue
            return urljoin(base_url, href)
    if fallback_href:
        return urljoin(base_url, fallback_href)
    return None


def _pick_listing_table(soup: BeautifulSoup, listing_selector: str | None):
    if listing_selector:
        table = soup.select_one(listing_selector)
        if table:
            headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
            return table, _match_headers(headers)

    target_table = None
    best_score = -1
    for table in soup.find_all("table"):
        headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
        if not headers:
            continue
        header_map = _match_headers(headers)
        score = len(header_map)
        if score > best_score:
            best_score = score
            target_table = (table, header_map)
    return target_table


def parse_listing_html(
    html: str,
    base_url: str,
    listing_selector: str | None = None,
    row_selector: str | None = None,
    view_details_selector: str | None = None,
) -> list[ListingRecord]:
    """Parse a CG RERA listing search HTML page into ListingRecord entries."""

    LOGGER.debug("Parsing listing HTML (selector: %s)", listing_selector)
    soup = BeautifulSoup(html, "html.parser")
    target_table = _pick_listing_table(soup, listing_selector)
    if target_table is None:
        LOGGER.warning("No listing table found in HTML")
        return []

    table, header_map = target_table
    LOGGER.debug("Found table with headers: %s", list(header_map.keys()))
    records: list[ListingRecord] = []
    if row_selector:
        rows = table.select(row_selector)
    else:
        rows = table.find_all("tr")

    LOGGER.info("Found %d rows in table, processing...", len(rows))
    for row_index, row in enumerate(rows, start=1):
        cells = row.find_all("td")
        if not cells:
            continue
        reg_no = _get_cell_text(cells, header_map.get("reg_no"))
        project_name = _get_cell_text(cells, header_map.get("project_name"))
        detail_url = _extract_detail_url(
            cells, header_map.get("detail_url"), base_url, view_details_selector
        )
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
            row_index=row_index,
        )
        records.append(record)
    LOGGER.info("Parsed %d valid listings from table", len(records))
    return records
