"""Configuration models for the CG RERA extraction framework."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel


class CrawlMode(str, Enum):
    """Supported crawl execution modes."""

    FULL = "FULL"
    INCREMENTAL = "INCREMENTAL"


class SearchFilterConfig(BaseModel):
    """Filters applied on the CG RERA listing search page."""

    districts: list[str]
    statuses: list[str]
    project_types: list[str] | None = None


class RunConfig(BaseModel):
    """Options controlling a full extraction run."""

    mode: CrawlMode
    search_filters: SearchFilterConfig
    output_base_dir: str
    state_code: str = "CG"


class BrowserConfig(BaseModel):
    """Browser/session level configuration."""

    driver: Literal["playwright", "selenium"] = "playwright"
    headless: bool = True
    slow_mo_ms: int | None = None
    default_timeout_ms: int = 20_000


class AppConfig(BaseModel):
    """Top-level application configuration."""

    run: RunConfig
    browser: BrowserConfig


__all__ = [
    "AppConfig",
    "BrowserConfig",
    "CrawlMode",
    "RunConfig",
    "SearchFilterConfig",
]
