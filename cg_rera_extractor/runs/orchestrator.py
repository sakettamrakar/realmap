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
from cg_rera_extractor.browser.session import PlaywrightBrowserSession
from cg_rera_extractor.config.models import AppConfig, RunMode
from cg_rera_extractor.detail.fetcher import fetch_and_save_details
from cg_rera_extractor.listing.models import ListingRecord
from cg_rera_extractor.listing.scraper import parse_listing_html
from cg_rera_extractor.parsing.mapper import map_raw_to_v1
from cg_rera_extractor.parsing.raw_extractor import extract_raw_from_html
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
            print(f"Running search for district={district} status={project_status}")
            LOGGER.info(
                "Running search for district=%s status=%s", district, project_status
            )
            try:
                listings_html = _run_search_and_get_listings(
                    session,
                    search_page_config.url,
                    search_page_config.selectors,
                    district,
                    project_status,
                    filters.project_types,
                    is_first_search=is_first_search,
                )
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
                if allowed is not None:
                    if allowed <= 0:
                        break
                    if len(listings) > allowed:
                        LOGGER.info(
                            "Global listing cap %s reached; trimming to %s entries",
                            listings_limit,
                            allowed,
                        )
                        listings = listings[:allowed]

                for record in listings:
                    record.run_id = run_id

                LOGGER.info(
                    "Parsed %d listings for %s / %s", len(listings), district, project_status
                )
                print(f"Parsed {len(listings)} listings for {district} / {project_status}")
                _save_listings_snapshot(
                    dirs["listings"], district, project_status, listings, listings_html
                )
                counts["listings_parsed"] += len(listings)
                counts["listings_scraped"] += len(listings)

                if run_config.mode != RunMode.LISTINGS_ONLY and listings:
                    fetch_and_save_details(
                        session,
                        search_page_config.selectors,
                        listings,
                        str(dirs["run_dir"]),
                        search_page_config.url,
                    )
                    counts["details_fetched"] += len(listings)
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.exception("Search failed for %s/%s", district, project_status)
                print(f"Error during search for {district}/{project_status}: {exc}")
                status.errors.append(str(exc))
            else:
                counts["search_combinations_processed"] += 1
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

    for path in (raw_html_dir, raw_extracted_dir, scraped_json_dir, listings_dir):
        path.mkdir(parents=True, exist_ok=True)

    return {
        "run_dir": run_dir,
        "raw_html": raw_html_dir,
        "raw_extracted": raw_extracted_dir,
        "scraped_json": scraped_json_dir,
        "listings": listings_dir,
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
    # For first search, navigate to URL. For subsequent searches, go back to preserve session
    if is_first_search:
        LOGGER.info("Navigating to search page: %s", search_url)
        session.goto(search_url)
    else:
        LOGGER.info("Going back to search page to preserve session")
        session.go_back()
        import time
        time.sleep(2)  # Wait for page to stabilize

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
    manual_wait_handled = apply_filters_or_fallback(session, selectors, filters, LOGGER)

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
        wait_for_captcha_solved()

    LOGGER.info("Waiting for results table to appear: %s", table_selector)
    print("  Waiting for results table to load...")
    session.wait_for_selector(table_selector, timeout_ms=20_000)
    if not table_visible:
        LOGGER.info("Results table now visible after filter/captcha flow")
    LOGGER.info("Results table loaded successfully")
    return session.get_page_html()


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
            raw = extract_raw_from_html(html, source_file=str(html_file))
            raw_path = dirs["raw_extracted"] / f"{html_file.stem}.json"
            _write_json(raw_path, raw.model_dump(mode="json"))

            v1_project = map_raw_to_v1(raw, state_code=state_code)
            v1_project = normalize_v1_project(v1_project)
            validation_messages = validate_v1_project(v1_project)
            if validation_messages:
                counts["dq_warnings"] += len(validation_messages)
                v1_project = v1_project.model_copy(
                    update={"validation_messages": validation_messages}
                )
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
