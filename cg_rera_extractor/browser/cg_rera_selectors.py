"""Central selectors and URLs for the CG RERA search experience."""
from __future__ import annotations

from cg_rera_extractor.browser.search_page_config import (
    DEFAULT_SEARCH_URL,
    SearchPageSelectors,
    default_search_page_selectors,
)


# Backwards-compatible exports; configuration overrides should use
# :func:`cg_rera_extractor.browser.search_page_config.get_search_page_config`.
SEARCH_URL = DEFAULT_SEARCH_URL
SEARCH_PAGE_SELECTORS = default_search_page_selectors()


__all__ = ["SEARCH_PAGE_SELECTORS", "SEARCH_URL", "SearchPageSelectors"]
