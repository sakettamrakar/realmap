"""High-level orchestration for CG RERA crawl runs."""
from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from cg_rera_extractor.browser.captcha_flow import wait_for_captcha_solved
from cg_rera_extractor.browser.search_page_config import (
    SearchPageConfigData,
    SearchPageSelectors,
    get_search_page_config,
)
from cg_rera_extractor.browser.search_page_flow import (
    SearchFilters,
    apply_filters_or_fallback,
    manual_filter_fallback,
)
from cg_rera_extractor.detail.preview_capture import load_preview_metadata
from cg_rera_extractor.detail.storage import load_listing_metadata
from cg_rera_extractor.browser.session import PlaywrightBrowserSession
from cg_rera_extractor.config.models import AppConfig, RunMode
from cg_rera_extractor.detail.fetcher import fetch_and_save_details
from cg_rera_extractor.listing.models import ListingRecord
from cg_rera_extractor.listing.scraper import parse_listing_html
from cg_rera_extractor.parsing.amenity_extractor import (
    extract_amenity_locations,
    extract_map_iframe_location,
    compute_centroid,
)
from cg_rera_extractor.parsing.mapper import map_raw_to_v1
from cg_rera_extractor.parsing.raw_extractor import extract_raw_from_html
from cg_rera_extractor.parsing.schema import PreviewArtifact, V1ReraLocation
from cg_rera_extractor.quality import normalize_v1_project, validate_v1_project
from cg_rera_extractor.runs.status import RunStatus

LOGGER = logging.getLogger(__name__)
MAX_LISTINGS_PER_SEARCH = 50


def run_crawl(app_config: AppConfig) -> RunStatus:
    """Orchestrate a single crawl run using configured parameters."""

    run_config = app_config.run
    filters = run_config.search_filters
    search_page_config: SearchPageConfigData = get_search_page_config(app_config)
    search_pairs = _compute_search_pairs(
        filters.districts, filters.statuses, run_config.max_search_combinations
    )
    run_id = _generate_run_id()
    started_at = datetime.now(timezone.utc)
    filters_used = {
        "districts": list(filters.districts),
        "statuses": list(filters.statuses),
        "project_types": list(filters.project_types or []),
    }

    counts = {
        "search_combinations_planned": len(search_pairs),
        "search_combinations_attempted": 0,
        "search_combinations_processed": 0,
        "listings_scraped": 0,
        "listings_parsed": 0,
        "details_fetched": 0,
        "projects_parsed": 0,
        "projects_mapped": 0,
        "dq_warnings": 0,
    }
    status = RunStatus(
        run_id=run_id,
        mode=str(run_config.mode.value if hasattr(run_config.mode, "value") else run_config.mode),
        started_at=started_at,
        filters_used=filters_used,
        counts=counts,
    )

    if run_config.mode == RunMode.DRY_RUN:
        _report_dry_run(search_pairs, run_config)
        status.finished_at = datetime.now(timezone.utc)
        return status

    dirs = _prepare_run_directories(Path(run_config.output_base_dir).expanduser(), run_id)
    print(
        f"Starting run {run_id} in {status.mode} mode. Output folder: {dirs['run_dir']}"
    )
    LOGGER.info(
        "Starting run %s in %s mode. Output folder: %s", run_id, status.mode, dirs["run_dir"]
    )
    session: PlaywrightBrowserSession | None = None
    listings_limit = run_config.max_total_listings

    try:
        session = PlaywrightBrowserSession(app_config.browser)
        session.start()

        for search_idx, (district, project_status) in enumerate(search_pairs):
            if _listing_limit_reached(listings_limit, counts["listings_scraped"]):
                break

            counts["search_combinations_attempted"] += 1
            is_first_search = (search_idx == 0)
            LOGGER.info(
                "Starting full crawl for district=%s status=%s (index %d/%d)",
                district,
                project_status,
                search_idx + 1,
                len(search_pairs),
            )
            print(f"Running search for district={district} status={project_status}")
            LOGGER.info(
                "Running search for district=%s status=%s", district, project_status
            )
            try:
                # Initial search (navigates, filters, solves captcha, waits for table)
                # This returns the HTML of the first page of results
                listings_html = _run_search_and_get_listings(
                    session,
                    search_page_config.url,
                    search_page_config.selectors,
                    district,
                    project_status,
                    filters.project_types,
                    is_first_search=is_first_search,
                )
                
                page_num = 1
                while True:
                    LOGGER.info("Processing page %d for %s/%s", page_num, district, project_status)
                    
                    # If this is not the first page, we need to get the current HTML
                    if page_num > 1:
                        listings_html = session.get_page_html()

                    listings = parse_listing_html(
                        listings_html,
                        search_page_config.url,
                        listing_selector=search_page_config.selectors.listing_table,
                        row_selector=search_page_config.selectors.row_selector,
                        view_details_selector=search_page_config.selectors.view_details_link,
                    )

                    if len(listings) > MAX_LISTINGS_PER_SEARCH:
                        LOGGER.warning(
                            "Parsed %s listings; truncating to %s for safety",
                            len(listings),
                            MAX_LISTINGS_PER_SEARCH,
                        )
                        status.warnings.append(
                            f"Truncated listings for {district}/{project_status} to {MAX_LISTINGS_PER_SEARCH}"
                        )
                        listings = listings[:MAX_LISTINGS_PER_SEARCH]

                    allowed = _remaining_listings(
                        listings_limit, counts["listings_scraped"]
                    )
                    
                    # If we have a limit, apply it
                    should_stop_after_this_batch = False
                    if allowed is not None:
                        if allowed <= 0:
                            LOGGER.info("Global listing limit reached before processing page %d", page_num)
                            break
                        if len(listings) > allowed:
                            LOGGER.info(
                                "Global listing cap %s reached; trimming to %s entries",
                                listings_limit,
                                allowed,
                            )
                            listings = listings[:allowed]
                            should_stop_after_this_batch = True

                    for record in listings:
                        record.run_id = run_id

                    LOGGER.info(
                        "Parsed %d listings for %s / %s (Page %d)", len(listings), district, project_status, page_num
                    )
                    print(f"Parsed {len(listings)} listings for {district} / {project_status} (Page {page_num})")
                    
                    _save_listings_snapshot(
                        dirs["listings"], f"{district}_p{page_num}", project_status, listings, listings_html
                    )
                    counts["listings_parsed"] += len(listings)
                    counts["listings_scraped"] += len(listings)

                    if run_config.mode != RunMode.LISTINGS_ONLY and listings:
                        try:
                            fetch_and_save_details(
                                session,
                                search_page_config.selectors,
                                listings,
                                str(dirs["run_dir"]),
                                search_page_config.url,
                                run_config.state_code,
                            )
                            counts["details_fetched"] += len(listings)
                        except Exception as exc:
                            LOGGER.exception("Detail fetching failed for %s/%s page %d: %s", district, project_status, page_num, exc)
                            print(f"Warning: Detail fetching failed: {exc}")
                            status.errors.append(f"Detail fetch failed for {district}/{project_status} page {page_num}: {str(exc)}")
                            # Continue processing even if detail fetch fails
                    
                    if should_stop_after_this_batch:
                        LOGGER.info("Stopping pagination as global limit reached.")
                        break
                        
                    # Try to go to next page
                    if not _go_to_next_page(session, search_page_config.selectors):
                        LOGGER.info("No more pages or next button disabled.")
                        break
                        
                    page_num += 1

            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.exception("Search failed for %s/%s", district, project_status)
                print(f"\nError during search for {district}/{project_status}: {exc}")
                print("Browser is still open. Check the browser window for error details.")
                import time
                time.sleep(5)  # Give user time to see what's in the browser
                status.errors.append(str(exc))
            else:
                counts["search_combinations_processed"] += 1
                LOGGER.info(
                    "Finished full crawl for district=%s status=%s (index %d/%d)",
                    district,
                    project_status,
                    search_idx + 1,
                    len(search_pairs),
                )
    finally:
        if session is not None:
            session.close()

    if run_config.mode == RunMode.FULL:
        _process_saved_html(dirs, run_config.state_code, counts, status)
    status.finished_at = datetime.now(timezone.utc)
    _write_json(dirs["run_dir"] / "run_report.json", status.to_serializable())
    print(f"Run {run_id} finished. Counts: {json.dumps(counts)}")
    LOGGER.info("Run %s finished. Counts: %s", run_id, counts)
    return status


def _generate_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return f"{timestamp}_{suffix}"


def _prepare_run_directories(base_dir: Path, run_id: str) -> dict[str, Path]:
    run_root = base_dir / "runs"
    run_dir = (run_root / f"run_{run_id}").resolve()
    raw_html_dir = run_dir / "raw_html"
    raw_extracted_dir = run_dir / "raw_extracted"
    scraped_json_dir = run_dir / "scraped_json"
    listings_dir = run_dir / "listings"
    previews_dir = run_dir / "previews"

    for path in (raw_html_dir, raw_extracted_dir, scraped_json_dir, listings_dir, previews_dir):
        path.mkdir(parents=True, exist_ok=True)

    return {
        "run_dir": run_dir,
        "raw_html": raw_html_dir,
        "raw_extracted": raw_extracted_dir,
        "scraped_json": scraped_json_dir,
        "listings": listings_dir,
        "previews": previews_dir,
    }


def _compute_search_pairs(
    districts: Iterable[str],
    statuses: Iterable[str],
    max_pairs: int | None,
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for district in districts:
        for status in statuses:
            pairs.append((district, status))
            if max_pairs is not None and len(pairs) >= max_pairs:
                return pairs
    return pairs


def _report_dry_run(
    search_pairs: list[tuple[str, str]],
    run_config,
) -> None:
    print("DRY RUN: no browser or network calls will be performed.")
    if run_config.max_search_combinations is not None:
        print(
            f"Search combinations capped at {run_config.max_search_combinations}; "
            f"planned {len(search_pairs)} pairs."
        )
    else:
        print(f"Planned {len(search_pairs)} search combinations (no cap).")

    for idx, (district, status_value) in enumerate(search_pairs, start=1):
        print(f" {idx}. district={district}, status={status_value}")

    if run_config.max_total_listings is not None:
        print(f"Global listing cap: {run_config.max_total_listings} (across all searches)")
    else:
        print("Global listing cap: none (unbounded)")


def _remaining_listings(limit: int | None, processed: int) -> int | None:
    if limit is None:
        return None
    return max(limit - processed, 0)


def _listing_limit_reached(limit: int | None, processed: int) -> bool:
    return limit is not None and processed >= limit


def _run_search_and_get_listings(
    session: PlaywrightBrowserSession,
    search_url: str,
    selectors: SearchPageSelectors,
    district: str,
    project_status: str,
    project_types: Iterable[str] | None,
    is_first_search: bool = True,
) -> str:
    """Run a search and return the HTML of the results page.
    
    Handles browser errors gracefully and waits for manual CAPTCHA solving.
    """
    try:
        LOGGER.info("Preparing search page for district=%s status=%s", district, project_status)
        # For first search, navigate to URL. For subsequent searches, go back to preserve session
        if is_first_search:
            LOGGER.info("Navigating to search page: %s", search_url)
            try:
                session.goto(search_url)
            except Exception as e:
                LOGGER.error("Navigation to search page failed: %s", e)
                print(f"\nFailed to navigate to {search_url}: {e}")
                raise
        else:
            LOGGER.info("Going back to search page to preserve session")
            try:
                session.go_back()
                import time
                time.sleep(2)  # Wait for page to stabilize
            except Exception as e:
                # If go_back fails (e.g., after detail page fetching), fall back to fresh navigation
                LOGGER.warning("go_back() failed: %s. Falling back to fresh navigation.", e)
                try:
                    session.goto(search_url)
                except Exception as e2:
                    LOGGER.error("Fresh navigation also failed: %s", e2)
                    print(f"\nFailed to navigate (even after go_back): {e2}")
                    raise

        table_selector = selectors.listing_table or selectors.results_table or "table"
        table_visible = False
        try:
            session.wait_for_selector(table_selector, timeout_ms=5_000)
            table_visible = True
            LOGGER.info("Listing container detected on initial load: %s", table_selector)
        except Exception:
            LOGGER.debug("Listing container not immediately visible; proceeding to apply filters")

        filters = SearchFilters(
            district=district,
            status=project_status,
            project_types=project_types,
        )
        LOGGER.info("Applying filters: district=%s, status=%s, types=%s", district, project_status, list(project_types) if project_types else "[]")
        
        try:
            manual_wait_handled = apply_filters_or_fallback(session, selectors, filters, LOGGER)
        except Exception as exc:
            LOGGER.warning("Filter application error (will try manual mode): %s", exc)
            manual_wait_handled = manual_filter_fallback(filters)

        if not manual_wait_handled and selectors.submit_button:
            try:
                LOGGER.info("Clicking search button automatically")
                print("  Clicking search button...")
                session.click(selectors.submit_button)
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.warning("Automatic search click failed: %s", exc)
                manual_wait_handled = manual_filter_fallback(filters)

        if not manual_wait_handled:
            LOGGER.info("Waiting for CAPTCHA to be solved manually")
            print("  Waiting for manual CAPTCHA solving...")
            try:
                wait_for_captcha_solved()
            except KeyboardInterrupt:
                LOGGER.warning("User interrupted CAPTCHA wait with Ctrl+C")
                print("CAPTCHA solve interrupted. Retrying...")
                manual_wait_handled = False
            except Exception as exc:
                LOGGER.warning("Error during CAPTCHA wait: %s", exc)
                print(f"Error during CAPTCHA wait: {exc}")
                manual_wait_handled = False

        try:
            LOGGER.info("Waiting for results table to appear: %s", table_selector)
            print("  Waiting for results table to load...")
            session.wait_for_selector(table_selector, timeout_ms=20_000)
            if not table_visible:
                LOGGER.info("Results table now visible after filter/captcha flow")
            LOGGER.info("Results table loaded successfully")
        except Exception as exc:
            LOGGER.warning("Results table selector timeout (may still have loaded): %s", exc)
            print(f"Note: Results table selector timeout: {exc}")
            print("Trying to proceed anyway - the table might still be on the page...")
            # Don't raise - just continue with whatever HTML we have
        
        try:
            return session.get_page_html()
        except Exception as exc:
            LOGGER.exception("Failed to get page HTML: %s", exc)
            print(f"\nFailed to retrieve page content: {exc}")
            print("This may indicate the browser was closed or page is no longer accessible.")
            raise
    
    except Exception as exc:
        LOGGER.exception("Search failed with exception: %s", exc)
        print(f"\nError during search: {exc}")
        print("Browser is still open. You can troubleshoot and try again.")
        raise


def _go_to_next_page(session: PlaywrightBrowserSession, selectors: SearchPageSelectors) -> bool:
    """Attempt to navigate to the next page of results.
    
    Returns True if navigation was successful, False if no next page exists.
    """
    next_btn_selector = selectors.next_page_button
    if not next_btn_selector:
        return False
        
    try:
        page = session.current_page()
        next_btn = page.locator(next_btn_selector)
        
        # Check visibility
        if not next_btn.is_visible():
            LOGGER.debug("Next button not visible")
            return False
            
        # Check if disabled (DataTables adds 'disabled' class to the button)
        class_attr = next_btn.get_attribute("class") or ""
        if "disabled" in class_attr:
            LOGGER.debug("Next button is disabled (end of results)")
            return False
            
        LOGGER.info("Navigating to next page of results...")
        print("  Clicking Next page...")
        next_btn.click()
        
        # Wait for table to update. 
        # Since we don't know if it's client-side or server-side, we wait a bit.
        # Ideally we would wait for a specific change, but a short sleep is safer than
        # complex logic that might flake.
        import time
        time.sleep(3) 
        
        return True
    except Exception as e:
        LOGGER.warning("Failed to go to next page: %s", e)
        return False


def _save_listings_snapshot(
    listings_dir: Path,
    district: str,
    project_status: str,
    listings: list[ListingRecord],
    listing_html: str,
) -> None:
    filename_base = (
        f"listings_{_sanitize_for_filename(district)}_"
        f"{_sanitize_for_filename(project_status)}"
    )
    payload = [asdict(record) for record in listings]
    _write_json(listings_dir / f"{filename_base}.json", payload)
    (listings_dir / f"{filename_base}.html").write_text(listing_html, encoding="utf-8")


def _sanitize_for_filename(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    return normalized.strip("_") or "all"


def _process_saved_html(
    dirs: dict[str, Path],
    state_code: str,
    counts: dict[str, int],
    status: RunStatus,
) -> None:
    raw_html_dir = dirs["raw_html"]
    for html_file in sorted(raw_html_dir.glob("*.html")):
        try:
            html = html_file.read_text(encoding="utf-8")
            
            # Extract registration number from filename if possible
            # Filename format: project_{state_code}_{reg_no}.html
            project_key = html_file.stem.replace("project_", "", 1)
            reg_no = None
            if project_key.startswith(f"{state_code}_"):
                reg_no = project_key[len(state_code) + 1:]
            
            raw = extract_raw_from_html(html, source_file=str(html_file), registration_number=reg_no)
            raw_path = dirs["raw_extracted"] / f"{html_file.stem}.json"
            _write_json(raw_path, raw.model_dump(mode="json"))

            v1_project = map_raw_to_v1(raw, state_code=state_code)
            
            # Load listing metadata (website_url, map coords, etc.) if available
            listing_meta = load_listing_metadata(str(dirs["run_dir"]), project_key)
            if listing_meta:
                website_url = listing_meta.get("website_url")
                if website_url:
                    updated_details = v1_project.project_details.model_copy(
                        update={"project_website_url": website_url}
                    )
                    v1_project = v1_project.model_copy(
                        update={"project_details": updated_details}
                    )
                    LOGGER.debug("Populated website_url=%s for %s", website_url, project_key)
            
            # Extract amenity locations with lat/lon from detail page
            amenity_locations = extract_amenity_locations(html)
            if amenity_locations:
                LOGGER.info(
                    "Extracted %d amenity locations from %s", len(amenity_locations), html_file.name
                )
                # Add amenity centroid as a "project_centroid" location
                centroid = compute_centroid(amenity_locations)
                if centroid:
                    centroid_loc = V1ReraLocation(
                        source_type="amenity_centroid",
                        latitude=centroid[0],
                        longitude=centroid[1],
                        particulars="Computed centroid of amenity locations",
                    )
                    amenity_locations.append(centroid_loc)
            else:
                amenity_locations = []
            
            # Extract Google Maps iframe location from detail page (if present)
            map_iframe_loc = extract_map_iframe_location(html)
            if map_iframe_loc:
                LOGGER.info(
                    "Extracted map iframe location from %s: lat=%s, lon=%s",
                    html_file.name,
                    map_iframe_loc.latitude,
                    map_iframe_loc.longitude,
                )
                amenity_locations.append(map_iframe_loc)
            
            # Add map coordinates from listing page (if available in listing metadata)
            if listing_meta:
                map_lat = listing_meta.get("map_latitude")
                map_lon = listing_meta.get("map_longitude")
                if map_lat is not None and map_lon is not None:
                    LOGGER.info(
                        "Adding listing page map location for %s: lat=%s, lon=%s",
                        project_key,
                        map_lat,
                        map_lon,
                    )
                    listing_map_loc = V1ReraLocation(
                        source_type="listing_map",
                        latitude=map_lat,
                        longitude=map_lon,
                        particulars="Google Maps marker from listing page",
                    )
                    amenity_locations.append(listing_map_loc)
            
            # Merge all locations into v1_project.rera_locations
            if amenity_locations:
                v1_project = v1_project.model_copy(
                    update={"rera_locations": amenity_locations}
                )
            
            v1_project = normalize_v1_project(v1_project)
            validation_messages = validate_v1_project(v1_project)
            if validation_messages:
                counts["dq_warnings"] += len(validation_messages)
                v1_project = v1_project.model_copy(
                    update={"validation_messages": validation_messages}
                )
            
            preview_dir = dirs.get("previews", dirs["run_dir"]) / project_key
            preview_metadata = load_preview_metadata(preview_dir)
            if preview_metadata:
                merged_previews: dict[str, PreviewArtifact] = dict(v1_project.previews)
                for key, artifact in preview_metadata.items():
                    if key in merged_previews:
                        base = PreviewArtifact(**merged_previews[key].model_dump())
                        base.artifact_type = artifact.artifact_type or base.artifact_type
                        base.files = artifact.files or base.files
                        base.notes = base.notes or artifact.notes
                        merged_previews[key] = base
                    else:
                        merged_previews[key] = artifact
                v1_project = v1_project.model_copy(update={"previews": merged_previews})
            v1_path = dirs["scraped_json"] / f"{html_file.stem}.v1.json"
            _write_json(
                v1_path,
                v1_project.model_dump(mode="json", exclude_none=True),
            )
            counts["projects_parsed"] += 1
            counts["projects_mapped"] += 1
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.exception("Failed to process %s", html_file)
            status.errors.append(str(exc))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = ["run_crawl"]
