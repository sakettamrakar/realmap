"""Configuration models for the CG RERA extraction framework."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class CrawlMode(str, Enum):
    """Supported crawl execution modes."""

    FULL = "full"
    INCREMENTAL = "incremental"


class SearchFilterConfig(BaseModel):
    """Filters applied on the CG RERA listing search page."""

    district: Optional[str] = Field(
        default=None,
        description="District filter exactly as shown in the CG RERA dropdown.",
    )
    tehsil: Optional[str] = Field(
        default=None,
        description="Tehsil filter applied after selecting the district.",
    )
    status: Optional[str] = Field(
        default=None,
        description="Project status filter (e.g. Registered, Completed).",
    )
    project_name: Optional[str] = Field(
        default=None,
        description="Optional free-text project name search value.",
    )
    promoter_name: Optional[str] = Field(
        default=None,
        description="Optional free-text promoter name search value.",
    )

    def summary(self) -> str:
        """Return a concise representation of the filter set."""

        return ", ".join(
            f"{field}={value}"
            for field, value in (
                ("district", self.district),
                ("tehsil", self.tehsil),
                ("status", self.status),
                ("project", self.project_name),
                ("promoter", self.promoter_name),
            )
            if value
        ) or "<no-filters>"


class BrowserConfig(BaseModel):
    """Browser/session level configuration."""

    provider: str = Field(
        default="playwright",
        description="Underlying automation provider (playwright/selenium/etc).",
    )
    headless: bool = Field(
        default=True,
        description="Run the browser in headless mode when possible.",
    )
    slow_mo_ms: int = Field(
        default=0,
        description="Optional delay between playwright actions to stabilise flows.",
    )
    manual_captcha: bool = Field(
        default=True,
        description="Whether the run expects the operator to manually solve captchas.",
    )
    default_timeout_ms: int = Field(
        default=15000,
        ge=1000,
        description="Default timeout for browser waits in milliseconds.",
    )


class RunConfig(BaseModel):
    """Options controlling a full extraction run."""

    crawl_mode: CrawlMode = Field(
        default=CrawlMode.FULL,
        description="Defines the crawl behaviour (full vs incremental).",
    )
    search_filters: List[SearchFilterConfig] = Field(
        default_factory=list,
        description="List of filter combinations to execute sequentially.",
    )
    max_projects: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of projects to collect (useful for smoke runs).",
    )
    output_dir: Path = Field(
        default=Path("outputs"),
        description="Base directory where run artefacts will be written.",
    )

    @field_validator("output_dir", mode="before")
    @classmethod
    def _convert_output_dir(cls, value: Path | str) -> Path:  # type: ignore[misc]
        if isinstance(value, Path):
            return value
        return Path(value)


class AppConfig(BaseModel):
    """Top-level application configuration."""

    run: RunConfig = Field(..., description="Execution level options.")
    browser: BrowserConfig = Field(
        default_factory=BrowserConfig,
        description="Browser/session options.",
    )
    data_dir: Path = Field(
        default=Path("data"),
        description="Directory containing cached HTML fixtures and other artefacts.",
    )

    @field_validator("data_dir", mode="before")
    @classmethod
    def _convert_data_dir(cls, value: Path | str) -> Path:  # type: ignore[misc]
        if isinstance(value, Path):
            return value
        return Path(value)

    @property
    def resolved_output_dir(self) -> Path:
        """Return the resolved output directory for the current run."""

        return self.run.output_dir.expanduser().resolve()


__all__ = [
    "AppConfig",
    "BrowserConfig",
    "CrawlMode",
    "RunConfig",
    "SearchFilterConfig",
]
