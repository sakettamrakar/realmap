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

    listing_table: str | None = None
    row_selector: str | None = None
    view_details_link: str | None = None
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


class GeocoderProvider(str, Enum):
    """Supported geocoding providers."""

    NOMINATIM = "nominatim"
    GOOGLE = "google"


class GeocoderConfig(BaseModel):
    """Geocoding provider and caching configuration."""

    provider: GeocoderProvider = GeocoderProvider.NOMINATIM
    api_key: str | None = None
    user_agent: str = "realmap-geocoder"
    base_url: str | None = None
    rate_limit_per_sec: float = 1.0
    cache_path: str = "data/geocode_cache.sqlite"
    request_timeout_sec: float = 10.0
    retries: int = 3
    backoff_factor: float = 1.5


class AmenityProvider(str, Enum):
    """Supported amenity providers."""

    OSM = "osm"
    GOOGLE = "google"


class AmenitiesConfig(BaseModel):
    """Amenity provider configuration and defaults."""

    provider: AmenityProvider = AmenityProvider.OSM
    api_key: str | None = None
    rate_limit_per_minute: float = 30.0
    search_radii_km: dict[str, list[float]] = {
        "school": [1.0, 3.0, 5.0],
        "college_university": [3.0, 5.0, 8.0],
        "hospital": [1.0, 3.0, 5.0],
        "clinic": [1.0, 3.0],
        "pharmacy": [0.5, 1.0, 2.0],
        "supermarket": [1.0, 3.0],
        "grocery_convenience": [0.5, 1.0, 2.0],
        "mall": [3.0, 5.0, 8.0],
        "bank_atm": [0.5, 1.0, 2.0],
        "restaurant_cafe": [1.0, 3.0, 5.0],
        "park_playground": [1.0, 3.0, 5.0],
        "transit_stop": [1.0, 3.0, 5.0, 10.0],
    }
    request_timeout_sec: float = 15.0
    retries: int = 3
    backoff_factor: float = 1.5


class AppConfig(BaseModel):
    """Top-level application configuration."""

    db: DatabaseConfig
    run: RunConfig
    browser: BrowserConfig
    geocoder: GeocoderConfig = GeocoderConfig()
    amenities: AmenitiesConfig = AmenitiesConfig()
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
    "GeocoderConfig",
    "GeocoderProvider",
    "AmenitiesConfig",
    "AmenityProvider",
]
