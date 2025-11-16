"""Data structures describing the outcome of a crawl run."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class RunStatus:
    """Summary of a single orchestrated crawl run."""

    run_id: str
    mode: str
    started_at: datetime
    finished_at: datetime | None = None
    filters_used: dict[str, Any] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


__all__ = ["RunStatus"]
