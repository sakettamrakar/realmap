from __future__ import annotations

import re
from typing import Dict

from bs4 import BeautifulSoup


LABEL_CLEAN_RE = re.compile(r"[^a-z0-9]+")


def _normalize_label(text: str) -> str:
    normalized = LABEL_CLEAN_RE.sub("_", text.strip().lower())
    return normalized.strip("_")


def _extract_value_text(cell) -> str:
    # Gather all visible text except preview buttons
    text_parts: list[str] = []
    for string in cell.stripped_strings:
        stripped = string.strip()
        if not stripped:
            continue
        if stripped.lower() == "preview":
            continue
        text_parts.append(stripped)

    joined = " ".join(text_parts)
    if joined:
        return joined

    if cell.find("button"):
        return "Preview"

    return ""


def extract_label_value_map(html: str) -> Dict[str, str]:
    """
    Parse the project detail HTML and return a dict mapping normalized label keys
    to their visible text values (excluding 'Preview' buttons, where possible).

    - Normalize label text:
      - Lowercase
      - Strip
      - Replace spaces and punctuation with underscores
    - For each row in the main detail tables:
      - First cell = label
      - Second cell = value cell
      - Value text should be the visible text only (ignore 'Preview' button label).
    - If value cell ONLY contains a Preview button and no text:
      - Store the special string "Preview" as the HTML value for that field.
    """

    soup = BeautifulSoup(html, "html.parser")
    label_values: Dict[str, str] = {}

    tables = soup.select("table")
    for table in tables:
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            label_text = cells[0].get_text(" ", strip=True)
            if not label_text:
                continue

            value_text = _extract_value_text(cells[1])
            label_key = _normalize_label(label_text)
            label_values[label_key] = value_text

    return label_values
