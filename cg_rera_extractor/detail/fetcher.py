"""Fetcher utilities for downloading project detail HTML pages."""

from __future__ import annotations

from cg_rera_extractor.browser.session import BrowserSession
from cg_rera_extractor.detail.storage import make_project_html_path, save_project_html
from cg_rera_extractor.listing.models import ListingRecord


def fetch_and_save_details(
    session: BrowserSession, listings: list[ListingRecord], output_base: str
) -> None:
    """Fetch detail pages for each listing and persist the HTML files."""

    for record in listings:
        if not record.detail_url:
            continue

        session.goto(record.detail_url)
        html = session.get_page_html()
        path = make_project_html_path(output_base, record.reg_no)
        save_project_html(path, html)

