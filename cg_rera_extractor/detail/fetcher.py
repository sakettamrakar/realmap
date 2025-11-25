"""Fetcher utilities for downloading project detail HTML pages."""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from urllib.parse import urljoin

from cg_rera_extractor.browser.search_page_config import SearchPageSelectors
from cg_rera_extractor.browser.session import BrowserSession
from cg_rera_extractor.detail.preview_capture import (
    build_preview_placeholders,
    capture_previews,
    save_preview_metadata,
)
from cg_rera_extractor.detail.storage import (
    make_project_html_path,
    make_project_key,
    save_project_html,
    save_listing_metadata,
)
from cg_rera_extractor.listing.models import ListingRecord


LOGGER = logging.getLogger(__name__)

# Regex patterns to extract coordinates from Google Maps embed URL
# Format: !2d<longitude>!3d<latitude> (note: 2d is longitude, 3d is latitude)
GOOGLE_MAPS_EMBED_PATTERN = re.compile(
    r"google\.com/maps/embed\?pb=.*?!2d([\d.]+)!3d([\d.]+)", re.IGNORECASE
)


def extract_map_coordinates_from_listing(
    session: BrowserSession,
    row_selector: str,
    row_index: int,
    timeout_ms: int = 5000,
) -> tuple[float | None, float | None]:
    """Click the map link in a listing row and extract coordinates from the popup.
    
    The CG RERA listing page has a map icon (fa-map-marker) that triggers a postback.
    This may either:
    1. Open a modal with a Google Maps iframe, or
    2. Navigate to a new page with the map
    
    This function handles both cases, extracts coordinates, and returns to the listing page.
    
    Args:
        session: Active browser session on the listing page.
        row_selector: CSS selector for table rows (e.g., "tr").
        row_index: 1-based index of the row to click.
        timeout_ms: Timeout for waiting for modal elements.
        
    Returns:
        Tuple of (latitude, longitude) or (None, None) if extraction fails.
    """
    try:
        page = session.current_page()
        original_url = page.url
        
        # Construct selector for the map link in this row
        # The map link has ID like: ContentPlaceHolder1_gv_ProjectList_lnk_View_map_0
        map_link_selector = f"a[id*='lnk_View_map_{row_index - 1}']"
        
        # Check if map link exists
        map_link = page.query_selector(map_link_selector)
        if not map_link:
            # Try alternative selector using fa-map-marker icon
            map_link_selector = f"{row_selector}:nth-of-type({row_index}) a:has(i.fa-map-marker)"
            map_link = page.query_selector(map_link_selector)
        
        if not map_link:
            LOGGER.debug("No map link found for row %d", row_index)
            return None, None
        
        LOGGER.debug("Clicking map link for row %d", row_index)
        
        # Click and wait briefly for response
        map_link.click()
        time.sleep(2)  # Wait for postback response
        
        # Check if we navigated to a different page or stayed on the same page
        current_url = page.url
        navigated = current_url != original_url
        
        lat, lon = None, None
        
        if navigated:
            LOGGER.debug("Map click caused navigation to: %s", current_url)
            # The postback opened a new page with the map
            # Wait for page to load and look for map/coordinates
            time.sleep(1)
            
        # Look for Google Maps iframe or map data in the page
        html = page.content()
        
        # Try to find Google Maps iframe
        iframes = page.query_selector_all("iframe")
        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            if "google.com/maps" in src:
                LOGGER.debug("Found Google Maps iframe: %s", src[:200])
                
                # Extract coordinates from the iframe src
                match = GOOGLE_MAPS_EMBED_PATTERN.search(src)
                if match:
                    lon_val = float(match.group(1))
                    lat_val = float(match.group(2))
                    
                    # Validate coordinates are in India range
                    if 6.0 <= lat_val <= 36.0 and 68.0 <= lon_val <= 98.0:
                        LOGGER.info("Extracted map coordinates: lat=%s, lon=%s", lat_val, lon_val)
                        lat, lon = lat_val, lon_val
                        break
                    else:
                        LOGGER.debug("Coordinates outside India range: lat=%s, lon=%s", lat_val, lon_val)
        
        # If we navigated away, go back to the listing page
        if navigated:
            LOGGER.debug("Navigating back to listing page after map extraction")
            page.go_back()
            time.sleep(2)  # Wait for listing page to load
            # Verify we're back on the listing page
            try:
                session.wait_for_selector(row_selector, timeout_ms=5000)
                LOGGER.debug("Successfully returned to listing page")
            except Exception:
                LOGGER.warning("Failed to verify return to listing page, may need to re-navigate")
        else:
            # We stayed on the same page, modal case - try to close it
            _close_map_modal(page)
        
        return lat, lon
        
    except Exception as exc:
        LOGGER.warning("Failed to extract map coordinates for row %d: %s", row_index, exc)
        # Try to recover - go back to listing page if we navigated away
        try:
            page = session.current_page()
            _close_map_modal(page)
            # Try going back just in case
            try:
                page.go_back()
                time.sleep(1)
            except Exception:
                pass
        except Exception:
            pass
        return None, None


def _close_map_modal(page) -> None:
    """Attempt to close any open modal on the page."""
    try:
        # Try common close button selectors
        close_selectors = [
            ".modal .close",
            ".modal-header .close",
            "button.close",
            "[data-dismiss='modal']",
            ".modal-footer button",
            "button:has-text('Close')",
            "button:has-text('×')",
        ]
        
        for selector in close_selectors:
            try:
                close_btn = page.query_selector(selector)
                if close_btn and close_btn.is_visible():
                    close_btn.click()
                    time.sleep(0.5)
                    LOGGER.debug("Closed modal using selector: %s", selector)
                    return
            except Exception:
                continue
        
        # If no close button found, try pressing Escape
        page.keyboard.press("Escape")
        time.sleep(0.5)
        LOGGER.debug("Closed modal using Escape key")
        
    except Exception as exc:
        LOGGER.debug("Failed to close modal: %s", exc)


def wait_for_page_loaded(session: BrowserSession, timeout: int = 30, main_selector: str | None = None) -> bool:
    """Wait until the page is fully loaded and log progress."""

    deadline = time.time() + timeout
    poll_interval = 2
    page = None

    try:
        page = session.current_page()  # type: ignore[attr-defined]
    except Exception as exc:
        LOGGER.debug("Unable to fetch current page for load checks: %s", exc)

    while time.time() < deadline:
        try:
            ready_state_complete = False
            if page is not None:
                ready_state = page.evaluate("document.readyState")
                ready_state_complete = ready_state == "complete"

            selector_ready = False
            if main_selector:
                try:
                    session.wait_for_selector(main_selector, timeout_ms=int(poll_interval * 1000))
                    selector_ready = True
                except Exception:
                    selector_ready = False

            if ready_state_complete or selector_ready:
                LOGGER.info("Page load complete.")
                return True
        except Exception as exc:
            LOGGER.debug("Page still settling (%s)", exc)

        LOGGER.debug("Page still loading...")
        time.sleep(poll_interval)

    LOGGER.warning("Page did not fully load within timeout, continuing anyway.")
    return False


def _log_loaded_page_state(session: BrowserSession) -> None:
    """Log current page URL and title for easier traceability."""

    try:
        page = session.current_page()  # type: ignore[attr-defined]
        LOGGER.info("Project details page loaded. URL=%s, title=%s", page.url, page.title())
    except Exception as exc:
        LOGGER.debug("Unable to log page state: %s", exc)


def fetch_and_save_details(
    session: BrowserSession,
    selectors: SearchPageSelectors,
    listings: list[ListingRecord],
    output_base: str,
    listing_page_url: str,
    state_code: str,
) -> None:
    """Fetch detail pages for each listing and persist the HTML files."""

    table_selector = selectors.listing_table or selectors.results_table or "table"
    row_locator = selectors.row_selector or "tr"
    total = len(listings)
    LOGGER.info("Starting detail fetch for %d listings", total)

    for idx, record in enumerate(listings, 1):
        if not record.detail_url:
            LOGGER.debug("Skipping %s - no detail URL", record.reg_no)
            continue

        try:
            project_label = record.project_name or record.reg_no
            uses_js_detail = record.detail_url.startswith("javascript") or "__doPostBack" in record.detail_url

            if uses_js_detail:
                if record.row_index is None:
                    LOGGER.warning(
                        "Skipping JS-only detail link for %s because row index is missing",
                        record.reg_no,
                    )
                    continue
                
                # Extract map coordinates from listing page BEFORE navigating to detail page
                # NOTE: This feature is currently disabled because clicking the map link on the
                # CG RERA listing page triggers a full page postback/navigation rather than
                # opening a modal. This disrupts the scraping flow. The coordinates are already
                # available from the amenities table on the detail page, so this is not critical.
                # 
                # To enable in the future, uncomment the following block:
                # if record.map_latitude is None and record.map_longitude is None:
                #     LOGGER.info("Extracting map coordinates for %s from listing page...", record.reg_no)
                #     lat, lon = extract_map_coordinates_from_listing(
                #         session, row_locator, record.row_index
                #     )
                #     if lat is not None and lon is not None:
                #         record.map_latitude = lat
                #         record.map_longitude = lon
                #         LOGGER.info("Map coordinates for %s: lat=%s, lon=%s", record.reg_no, lat, lon)
                #     else:
                #         LOGGER.debug("No map coordinates found for %s", record.reg_no)
                
                view_locator = selectors.view_details_link or "a"
                target_selector = f"{row_locator}:nth-of-type({record.row_index}) {view_locator}"
                LOGGER.info("[%d/%d] Fetching details for %s (JS click method)", idx, total, record.reg_no)
                print(f"[{idx}/{total}] Fetching details for {record.reg_no} (JavaScript click)...")
                LOGGER.info("Clicking project #%d: %s", idx, project_label)

                # Click the link - this triggers an ASP.NET postback
                session.click(target_selector)
                LOGGER.debug("Project details page click submitted; waiting for page to load...")
                wait_for_page_loaded(session, timeout=30)
                _log_loaded_page_state(session)
                
                # Dynamic wait for detail page content
                # We look for a common element on the detail page, e.g. "Project Detail" header or similar
                # Based on raw_extractor, we expect headings like "Project Detail" or "Promoter Details"
                # Let's wait for a generic indicator that we are NOT on the search page anymore
                try:
                    # Dynamic wait for detail page content
                    # We poll for characteristic text that appears on the detail page.
                    # We also handle errors that occur if the page is in the middle of navigation.

                    detail_loaded = False
                    for _ in range(20): # Wait up to 20 seconds
                        try:
                            html = session.get_page_html()
                            # Check for characteristic detail page text that is NOT on search page
                            if "Project Detail" in html or "Promoter Detail" in html:
                                detail_loaded = True
                                break
                        except Exception as e:
                            # If page is navigating, content retrieval might fail. 
                            # This is expected during the transition.
                            LOGGER.debug("Ignored error during detail wait check (likely navigating): %s", e)
                        
                        time.sleep(1)
                        
                    if not detail_loaded:
                        LOGGER.warning("Timed out waiting for detail page content (Project/Promoter Detail)")
                        # Proceed anyway, maybe it's a different format or just slow
                
                except Exception as e:
                    LOGGER.warning("Unexpected error while waiting for detail page load: %s", e)
                    # Fallback to sleep
                    time.sleep(5)

                # Try to get content with multiple retries
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        html = session.get_page_html()
                        if html and len(html) > 100:  # Sanity check that we got real content
                            LOGGER.debug("Successfully retrieved detail page content on attempt %d", attempt + 1)
                            break
                    except Exception as e:
                        LOGGER.warning("Attempt %d to get page content failed: %s", attempt + 1, e)
                        if attempt < max_retries - 1:
                            time.sleep(1)
                        else:
                            raise
            else:
                LOGGER.info("[%d/%d] Fetching details for %s (direct URL)", idx, total, record.reg_no)
                print(f"[{idx}/{total}] Fetching details for {record.reg_no} (direct navigation)...")
                LOGGER.info("Clicking project #%d: %s", idx, project_label)
                session.goto(urljoin(listing_page_url, record.detail_url))
                LOGGER.debug("Project details page navigation submitted; waiting for page to load...")
                wait_for_page_loaded(session, timeout=30)
                _log_loaded_page_state(session)
                html = session.get_page_html()

            project_key = make_project_key(state_code, record.reg_no)
            path = make_project_html_path(output_base, project_key)
            save_project_html(path, html)
            LOGGER.info("Saved detail page for %s to %s", record.reg_no, path)
            
            # Save listing metadata (website_url, district, map coords, etc.) alongside HTML
            # This allows correlating listing data with detail data during processing
            listing_meta = {
                "reg_no": record.reg_no,
                "project_name": record.project_name,
                "promoter_name": record.promoter_name,
                "district": record.district,
                "tehsil": record.tehsil,
                "status": record.status,
                "website_url": record.website_url,
                "map_latitude": record.map_latitude,
                "map_longitude": record.map_longitude,
                "detail_url": record.detail_url,
            }
            save_listing_metadata(output_base, project_key, listing_meta)
            LOGGER.debug("Saved listing metadata for %s", record.reg_no)

            try:
                LOGGER.info("Starting data extraction for current project...")
                LOGGER.info("Collecting basic project fields...")
                preview_placeholders = build_preview_placeholders(
                    html,
                    source_file=path,
                    state_code=state_code,
                    registration_number=record.reg_no,
                    project_name=record.project_name,
                )
                LOGGER.info("Locating preview section...")
                if preview_placeholders and hasattr(session, "current_page"):
                    page = session.current_page()  # type: ignore[attr-defined]
                    context = session.current_context()  # type: ignore[attr-defined]
                    LOGGER.info("Starting download of artifacts for current project...")
                    captured = capture_previews(
                        page=page,
                        context=context,
                        project_key=project_key,
                        output_base=Path(output_base),
                        preview_placeholders=preview_placeholders,
                    )
                    LOGGER.info("All artifacts downloaded for current project.")
                    if captured:
                        save_preview_metadata(Path(output_base), project_key, captured)
                LOGGER.info("Finished data extraction for current project.")
                print(f"[{idx}/{total}] Preview capture completed for {record.reg_no}")
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.warning("Preview capture failed for %s: %s", record.reg_no, exc)
                print(f"Warning: Preview capture failed for {record.reg_no}: {exc}")

            # Navigate back to the listing page after each detail fetch to keep the
            # search context alive for subsequent listings and search combinations.
            if uses_js_detail:
                back_description = "(JavaScript method preserves filters)"
            else:
                back_description = "(direct navigation)"

            LOGGER.info("Navigating back to search/list page to pick next project... %s", back_description)
            try:
                # Handle "Confirm Form Resubmission" dialog which might appear on go_back
                if hasattr(session, "current_page"):
                    page = session.current_page()
                    # Add a listener to accept any dialogs (like form resubmission confirmation)
                    # Note: This might stack listeners if not careful, but for this script it's acceptable
                    page.on("dialog", lambda dialog: dialog.accept())

                session.go_back()
                wait_for_page_loaded(session, timeout=30, main_selector=table_selector)
                LOGGER.info("Search/list page loaded again, continuing to next project.")

            except Exception as e:
                # Handle ERR_CACHE_MISS by reloading, which should trigger the form resubmission dialog
                if "ERR_CACHE_MISS" in str(e) and hasattr(session, "current_page"):
                    LOGGER.warning("go_back() failed with ERR_CACHE_MISS. Attempting reload to resubmit form...")
                    try:
                        session.current_page().reload()
                        wait_for_page_loaded(session, timeout=30, main_selector=table_selector)
                        LOGGER.info("Reloaded page successfully (form resubmitted).")
                        # Clear the exception so we don't log the warning below
                        e = None 
                    except Exception as reload_exc:
                        LOGGER.error("Reload failed: %s", reload_exc)
                
                if e:
                    LOGGER.warning("go_back() failed after fetching details: %s. Continuing to next listing.", e)
                # The filter state is lost, but we can continue processing other listings
            LOGGER.debug("Listing page navigation handled")
        
        except Exception as exc:
            # Main catch-all for entire detail fetch iteration
            LOGGER.exception("Failed to fetch details for %s: %s", record.reg_no, exc)
            print(f"Skipping {record.reg_no} - error fetching details: {exc}")
            
            if "Target closed" in str(exc) or "Session closed" in str(exc):
                LOGGER.error("Browser session appears to be closed. Aborting detail fetch.")
                raise exc

            # Attempt to recover navigation state if we failed in the middle of a detail fetch
            # We might be stuck on the detail page or an error page.
            # We need to ensure we are back on the listing page for the next iteration.
            try:
                LOGGER.info("Attempting to recover navigation state after error...")
                # If we are on the detail page (or not on search page), go back
                # How do we know? We can check for the search table.
                try:
                    session.wait_for_selector(table_selector, timeout_ms=2000)
                    LOGGER.info("Search table found, we are likely on the listing page.")
                except Exception:
                    LOGGER.info("Search table not found, attempting go_back()...")
                    session.go_back()
                    session.wait_for_selector(table_selector, timeout_ms=10_000)
                    LOGGER.info("Recovered to listing page.")
            except Exception as rec_exc:
                LOGGER.error("Failed to recover navigation state: %s", rec_exc)
                # If we can't recover, the next iteration will likely fail too.
                # We might want to break or re-navigate to search url?
                # For now, just continue and let the next iteration try (or fail).

            # Continue processing remaining listings instead of crashing
            continue
        
        
    LOGGER.info("Detail fetch complete for all %d listings", total)

