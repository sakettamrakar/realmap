"""Utilities for converting CG RERA project detail HTML to raw sections."""

from __future__ import annotations

import re
from collections import OrderedDict
from datetime import datetime
from typing import Iterable, List, Optional

from bs4 import BeautifulSoup, NavigableString, Tag

from .schema import FieldRecord, FieldValueType, RawExtractedProject, SectionRecord

HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6", "strong")
DEFAULT_SECTION_TITLE = "General"


def extract_raw_from_html(html: str, source_file: str) -> RawExtractedProject:
    """Parse project detail HTML and return structured raw sections."""

    soup = BeautifulSoup(html, "html.parser")
    label_tags = soup.find_all("label")

    section_map: "OrderedDict[str, List[FieldRecord]]" = OrderedDict()

    for label in label_tags:
        label_text = _clean_label_text(label.get_text(" ", strip=True))
        if not label_text:
            continue

        section_title = _find_section_title(label)
        value_text, links = _extract_value_and_links(label)
        value_text = value_text or None
        normalized_value = _normalize_whitespace(value_text)
        links = list(dict.fromkeys(links))
        field_record = FieldRecord(
            label=label_text,
            value=normalized_value,
            value_type=_infer_value_type(normalized_value, links),
            links=links,
        )

        if section_title not in section_map:
            section_map[section_title] = []
        section_map[section_title].append(field_record)

    sections = [
        SectionRecord(section_title_raw=title, fields=fields)
        for title, fields in section_map.items()
    ]

    return RawExtractedProject(source_file=source_file, sections=sections)


def _clean_label_text(text: str) -> str:
    return text.strip().rstrip(":")


def _find_section_title(label_tag: Tag) -> str:
    heading = label_tag.find_previous(_is_heading_tag)
    if heading:
        heading_text = heading.get_text(" ", strip=True)
        if heading_text:
            return heading_text
    return DEFAULT_SECTION_TITLE


def _is_heading_tag(tag: Optional[Tag]) -> bool:
    return bool(tag and tag.name and tag.name.lower() in HEADING_TAGS)


def _extract_value_and_links(label_tag: Tag) -> tuple[str, List[str]]:
    # table-based layout support
    parent = label_tag.parent if isinstance(label_tag.parent, Tag) else None
    if parent and parent.name == "td":
        sibling_td = parent.find_next_sibling("td")
        if sibling_td:
            text, links = _text_and_links_from_tag(sibling_td)
            if text:
                return text, links

    # inline label layout
    for sibling in label_tag.next_siblings:
        if isinstance(sibling, NavigableString):
            text = sibling.strip()
            if text:
                return text, []
        elif isinstance(sibling, Tag):
            text, links = _text_and_links_from_tag(sibling)
            if text:
                return text, links

    # fallback to parent text without the label contents
    if parent:
        parent_text = parent.get_text(" ", strip=True)
        label_text = label_tag.get_text(" ", strip=True)
        if parent_text and label_text and parent_text != label_text:
            cleaned = parent_text.replace(label_text, "", 1).strip(" :\n\t")
            if cleaned:
                links = _collect_links(parent)
                return cleaned, links

    return "", []


def _text_and_links_from_tag(tag: Tag) -> tuple[str, List[str]]:
    text = tag.get_text(" ", strip=True)
    links = _collect_links(tag)
    return text, links


def _collect_links(tag: Tag) -> List[str]:
    links: List[str] = []
    if tag.name == "a" and tag.has_attr("href"):
        href = tag["href"].strip()
        if href:
            links.append(href)
    for anchor in tag.find_all("a"):
        if anchor.has_attr("href"):
            href = anchor["href"].strip()
            if href:
                links.append(href)
    return links


def _normalize_whitespace(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    collapsed = " ".join(value.split())
    return collapsed if collapsed else None


_DATE_PATTERNS: Iterable[str] = (
    r"\b\d{2}/\d{2}/\d{4}\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
)


def _infer_value_type(value: Optional[str], links: List[str]) -> FieldValueType:
    if value:
        lowered = value.lower()
        if lowered.startswith("http://") or lowered.startswith("https://"):
            return FieldValueType.URL

        if _looks_like_number(value):
            return FieldValueType.NUMBER

        if _looks_like_date(value):
            return FieldValueType.DATE

    if links:
        return FieldValueType.URL

    if value:
        return FieldValueType.TEXT

    return FieldValueType.UNKNOWN


def _looks_like_number(value: str) -> bool:
    number_pattern = re.compile(r"^-?\d{1,3}(?:,\d{3})*(?:\.\d+)?$|^-?\d+(?:\.\d+)?$")
    return bool(number_pattern.match(value.replace(" ", "")))


def _looks_like_date(value: str) -> bool:
    for pattern in _DATE_PATTERNS:
        if re.search(pattern, value):
            if _try_parse_date(value):
                return True
    return False


def _try_parse_date(value: str) -> bool:
    value = value.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False

