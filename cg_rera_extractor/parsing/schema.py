"""Data structures used by the raw HTML extractor."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class FieldValueType(str, Enum):
    """Enumeration of supported raw field value classifications."""

    TEXT = "TEXT"
    NUMBER = "NUMBER"
    DATE = "DATE"
    URL = "URL"
    UNKNOWN = "UNKNOWN"


@dataclass(slots=True)
class FieldRecord:
    """Represents a single label/value pair extracted from the HTML."""

    label: str
    value: Optional[str]
    value_type: FieldValueType
    links: List[str] = field(default_factory=list)


@dataclass(slots=True)
class SectionRecord:
    """Collection of fields grouped under the same section heading."""

    section_title_raw: str
    fields: List[FieldRecord] = field(default_factory=list)


@dataclass(slots=True)
class RawExtractedProject:
    """Top-level structure returned by the HTML parser."""

    source_file: str
    sections: List[SectionRecord] = field(default_factory=list)

