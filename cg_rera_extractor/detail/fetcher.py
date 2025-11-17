"""Fetcher utilities for downloading project detail HTML pages."""

from __future__ import annotations

import logging
from urllib.parse import urljoin

from cg_rera_extractor.browser.search_page_config import SearchPageSelectors
from cg_rera_extractor.browser.session import BrowserSession
from cg_rera_extractor.detail.storage import make_project_html_path, save_project_html
from cg_rera_extractor.listing.models import ListingRecord


LOGGER = logging.getLogger(__name__)

def fetch_and_save_details(
    session: BrowserSession,
    selectors: SearchPageSelectors,
    listings: list[ListingRecord],
    output_base: str,
    listing_page_url: str,
) -> None:
    """Fetch detail pages for each listing and persist the HTML files."""

    table_selector = selectors.listing_table or selectors.results_table or "table"
    total = len(listings)
    LOGGER.info("Starting detail fetch for %d listings", total)

    for idx, record in enumerate(listings, 1):
        if not record.detail_url:
            LOGGER.debug("Skipping %s - no detail URL", record.reg_no)
            continue

        uses_js_detail = record.detail_url.startswith("javascript") or "__doPostBack" in record.detail_url

        if uses_js_detail:
            if record.row_index is None:
                LOGGER.warning(
                    "Skipping JS-only detail link for %s because row index is missing",
                    record.reg_no,
                )
                continue
            row_locator = selectors.row_selector or "tr"
            view_locator = selectors.view_details_link or "a"
            target_selector = f"{row_locator}:nth-of-type({record.row_index}) {view_locator}"
            LOGGER.info("[%d/%d] Fetching details for %s (JS click method)", idx, total, record.reg_no)
            print(f"[{idx}/{total}] Fetching details for {record.reg_no} (JavaScript click)...")
            session.click(target_selector)
        else:
            LOGGER.info("[%d/%d] Fetching details for %s (direct URL)", idx, total, record.reg_no)
            print(f"[{idx}/{total}] Fetching details for {record.reg_no} (direct navigation)...")
            session.goto(urljoin(listing_page_url, record.detail_url))

        html = session.get_page_html()
        path = make_project_html_path(output_base, record.reg_no)
        save_project_html(path, html)
        LOGGER.info("Saved detail page for %s to %s", record.reg_no, path)

        # Navigate back to the listing page if we had to click within the grid.
        # This preserves the filter selections without page refresh.
        if uses_js_detail:
            LOGGER.debug("Navigating back to listing page (JavaScript method preserves filters)")
            session.go_back()
            session.wait_for_selector(table_selector)
            LOGGER.debug("Listing page reloaded with filters preserved")
        
    LOGGER.info("Detail fetch complete for all %d listings", total)

