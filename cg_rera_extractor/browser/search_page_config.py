"""Configuration helpers for the CG RERA search page."""
from __future__ import annotations

from dataclasses import dataclass

from cg_rera_extractor.config.models import AppConfig, SearchPageSelectorsConfig


# Default search page URL; can be overridden via config.
DEFAULT_SEARCH_URL = "https://rera.cgstate.gov.in/Approved_project_List.aspx"


@dataclass(frozen=True)
class SearchPageSelectors:
    """Selectors used on the CG RERA project search page."""

    listing_table: str | None = "#ContentPlaceHolder1_gv_ProjectList"
    row_selector: str | None = "#ContentPlaceHolder1_gv_ProjectList > tbody > tr"
    view_details_link: str | None = "a[id*='gv_ProjectList_lnk_View']"
    district: str | None = "#ContentPlaceHolder1_District_Name"
    status: str | None = "#ContentPlaceHolder1_ApplicantType"
    project_type: str | None = "#ContentPlaceHolder1_DropDownList2"
    submit_button: str | None = "#ContentPlaceHolder1_Button1"
    results_table: str | None = "#ContentPlaceHolder1_gv_ProjectList"


@dataclass(frozen=True)
class SearchPageConfigData:
    """Fully resolved search page configuration for runtime use."""

    url: str
    selectors: SearchPageSelectors


def _merge_selectors(
    config_selectors: SearchPageSelectorsConfig | None,
) -> SearchPageSelectors:
    defaults = SearchPageSelectors()
    if config_selectors is None:
        return defaults

    return SearchPageSelectors(
        listing_table=config_selectors.listing_table or defaults.listing_table,
        row_selector=config_selectors.row_selector or defaults.row_selector,
        view_details_link=
            config_selectors.view_details_link or defaults.view_details_link,
        district=config_selectors.district or defaults.district,
        status=config_selectors.status or defaults.status,
        project_type=config_selectors.project_type or defaults.project_type,
        submit_button=config_selectors.submit_button or defaults.submit_button,
        results_table=config_selectors.results_table or defaults.results_table,
    )


def get_search_page_config(app_config: AppConfig) -> SearchPageConfigData:
    """Resolve search page URL and selectors from config (with defaults)."""

    search_config = getattr(app_config, "search_page", None)
    url = DEFAULT_SEARCH_URL
    selectors_config = None

    if search_config is not None:
        url = search_config.url or url
        selectors_config = search_config.selectors

    selectors = _merge_selectors(selectors_config)
    return SearchPageConfigData(url=url, selectors=selectors)


def default_search_page_selectors() -> SearchPageSelectors:
    """Expose defaults for legacy imports and tests."""

    return SearchPageSelectors()


__all__ = [
    "DEFAULT_SEARCH_URL",
    "SearchPageConfigData",
    "SearchPageSelectors",
    "default_search_page_selectors",
    "get_search_page_config",
]
