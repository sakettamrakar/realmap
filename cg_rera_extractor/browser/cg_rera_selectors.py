"""Central selectors and URLs for the CG RERA search experience."""
from __future__ import annotations

from dataclasses import dataclass


SEARCH_URL = "https://rera.cgstate.gov.in/Approved_project_List.aspx"


@dataclass(frozen=True)
class SearchPageSelectors:
    """CSS selectors used on the CG RERA project search page."""

    district_select: str = "select[name='district']"
    status_select: str = "select[name='status']"
    project_type_select: str = "select[name='project_type']"
    search_button: str = "button[type='submit']"
    results_table: str = "table"


SEARCH_PAGE_SELECTORS = SearchPageSelectors()


__all__ = ["SEARCH_PAGE_SELECTORS", "SEARCH_URL", "SearchPageSelectors"]
