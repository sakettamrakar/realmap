"""Search page automation with manual fallback support."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

from cg_rera_extractor.browser.search_page_config import SearchPageSelectors
from cg_rera_extractor.browser.session import BrowserSession


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchFilters:
    """Resolved search filters for a single listing request."""

    district: str
    status: str
    project_types: Iterable[str] | None = None


def apply_filters_or_fallback(
    session: BrowserSession,
    selectors: SearchPageSelectors,
    filters: SearchFilters,
    logger: logging.Logger | None = None,
) -> bool:
    """Attempt to apply filters; fall back to manual instructions on failure.

    Returns ``True`` if manual mode was triggered (and the function already
    waited for user confirmation), otherwise ``False``.
    """

    active_logger = logger or LOGGER

    try:
        active_logger.debug(f"Attempting to apply district filter with selector: {selectors.district}")
        _apply_select(session, selectors.district, filters.district, "district")
        active_logger.debug("District filter applied successfully")
        
        active_logger.debug(f"Attempting to apply status filter with selector: {selectors.status}")
        _apply_select(session, selectors.status, filters.status, "status")
        active_logger.debug("Status filter applied successfully")
        
        if filters.project_types:
            active_logger.debug(f"Attempting to apply project type filter with selector: {selectors.project_type}")
            _apply_select(
                session,
                selectors.project_type,
                list(filters.project_types),
                "project_type",
            )
            active_logger.debug("Project type filter applied successfully")
        
        active_logger.info(
            "Applied filters automatically for district=%s status=%s",
            filters.district,
            filters.status,
        )
        return False
    except Exception as exc:  # pragma: no cover - defensive safety net
        active_logger.exception("Automatic filter selection failed: %s", exc)
        print(f"\nAutomatic filters failed: {exc}")
        return manual_filter_fallback(filters)


def _apply_select(
    session: BrowserSession, selector: str | None, value, label: str
) -> None:
    if not selector:
        raise ValueError(f"Missing selector for {label}")
    session.select_option(selector, value)


def manual_filter_fallback(filters: SearchFilters) -> bool:
    print("\n=== MANUAL FILTER MODE ===")
    print("Could not apply filters automatically (selectors not found or page changed).")
    print("Please:")
    print("  1) Manually select district/status/project type as desired.")
    print("  2) Solve the CAPTCHA.")
    print("  3) Click the Search button if needed (the table may already be loaded).")
    print("  4) When the listing results are fully visible, come back here and press ENTER.")
    print(
        f"Active filters: district={filters.district!r}, status={filters.status!r}, "
        f"project_types={list(filters.project_types) if filters.project_types else '[]'}"
    )
    input("Press ENTER here after you have clicked Search and listings are visible...")
    return True


__all__ = ["SearchFilters", "apply_filters_or_fallback", "manual_filter_fallback"]
