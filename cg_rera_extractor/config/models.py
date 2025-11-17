"""Configuration models for the CG RERA extraction framework."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, model_validator

from cg_rera_extractor.config.env import ensure_database_url


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


class SearchPageSelectorsConfig(BaseModel):
    """Override selectors for the CG RERA search page."""

    district: str | None = None
    status: str | None = None
    project_type: str | None = None
    submit_button: str | None = None
    results_table: str | None = None


class SearchPageConfig(BaseModel):
    """Search page URL and selector overrides."""

    url: str | None = None
    selectors: SearchPageSelectorsConfig | None = None


class RunConfig(BaseModel):
    """Options controlling a full extraction run."""

    mode: RunMode = RunMode.FULL
    search_filters: SearchFilterConfig
    output_base_dir: str
    state_code: str = "CG"
    max_search_combinations: int | None = 10
    max_total_listings: int | None = 200


class DatabaseConfig(BaseModel):
    """Database connectivity settings."""

    url: str

    @model_validator(mode="before")
    def populate_from_env(cls, values: dict[str, str]) -> dict[str, str]:
        """Populate the database URL from ``DATABASE_URL`` if missing."""

        url = values.get("url") if isinstance(values, dict) else None
        if not url:
            env_url = ensure_database_url()
            values = {**(values or {}), "url": env_url}
        return values


class BrowserConfig(BaseModel):
    """Browser/session level configuration."""

    driver: Literal["playwright", "selenium"] = "playwright"
    headless: bool = True
    slow_mo_ms: int | None = None
    default_timeout_ms: int = 20_000


class AppConfig(BaseModel):
    """Top-level application configuration."""

    db: DatabaseConfig
    run: RunConfig
    browser: BrowserConfig
    search_page: SearchPageConfig = SearchPageConfig()


__all__ = [
    "AppConfig",
    "BrowserConfig",
    "RunMode",
    "RunConfig",
    "SearchFilterConfig",
    "SearchPageConfig",
    "SearchPageSelectorsConfig",
    "DatabaseConfig",
]
