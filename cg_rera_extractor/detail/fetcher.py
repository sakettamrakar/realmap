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

    for record in listings:
        if not record.detail_url:
            continue

        if record.detail_url.startswith("javascript") or "__doPostBack" in record.detail_url:
            if record.row_index is None:
                LOGGER.warning(
                    "Skipping JS-only detail link for %s because row index is missing",
                    record.reg_no,
                )
                continue
            row_locator = selectors.row_selector or "tr"
            view_locator = selectors.view_details_link or "a"
            target_selector = f"{row_locator}:nth-of-type({record.row_index}) {view_locator}"
            LOGGER.info("Clicking detail link via selector: %s", target_selector)
            session.click(target_selector)
        else:
            session.goto(urljoin(listing_page_url, record.detail_url))

        html = session.get_page_html()
        path = make_project_html_path(output_base, record.reg_no)
        save_project_html(path, html)

        # Navigate back to the listing page if we had to click within the grid.
        if record.detail_url.startswith("javascript") or "__doPostBack" in record.detail_url:
            session.goto(listing_page_url)
            session.wait_for_selector(table_selector)

