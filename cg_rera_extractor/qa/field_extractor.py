from __future__ import annotations

import re
from typing import Dict

from cg_rera_extractor.parsing.raw_extractor import extract_raw_from_html


LABEL_CLEAN_RE = re.compile(r"[^a-z0-9]+")


def _normalize_label(text: str) -> str:
    normalized = LABEL_CLEAN_RE.sub("_", text.strip().lower())
    return normalized.strip("_")


def extract_label_value_map(html: str) -> Dict[str, str]:
    """
    Parse the project detail HTML and return a dict mapping normalized label keys
    to their visible text values using the same raw extractor as the parser.
    """

    raw = extract_raw_from_html(html, source_file="qa")
    label_values: Dict[str, str] = {}
    for section in raw.sections:
        for field in section.fields:
            if not field.label:
                continue
            label_key = _normalize_label(field.label)
            value = field.value or ""
            if not value and field.preview_present:
                value = "Preview"
            label_values[label_key] = value

    return label_values
