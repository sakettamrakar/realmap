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
    warnings: list[str] = field(default_factory=list)

    def to_serializable(self) -> dict[str, Any]:
        """Convert the run status into a JSON-serializable dictionary."""

        return {
            "run_id": self.run_id,
            "mode": self.mode,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "filters_used": self.filters_used,
            "counts": self.counts,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


__all__ = ["RunStatus"]
