"""Configuration models for the CG RERA extraction framework."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel


class RunMode(str, Enum):
    """Supported run execution modes."""

    DRY_RUN = "DRY_RUN"
    LISTINGS_ONLY = "LISTINGS_ONLY"
    FULL = "FULL"


class SearchFilterConfig(BaseModel):
    """Filters applied on the CG RERA listing search page."""

    districts: list[str]
    statuses: list[str]
    project_types: list[str] | None = None


class RunConfig(BaseModel):
    """Options controlling a full extraction run."""

    mode: RunMode = RunMode.FULL
    search_filters: SearchFilterConfig
    output_base_dir: str
    state_code: str = "CG"
    max_search_combinations: int | None = 10
    max_total_listings: int | None = 200


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
    "RunMode",
    "RunConfig",
    "SearchFilterConfig",
]
