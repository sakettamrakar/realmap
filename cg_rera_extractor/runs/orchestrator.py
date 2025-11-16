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
from cg_rera_extractor.browser.cg_rera_selectors import (
    SEARCH_PAGE_SELECTORS,
    SEARCH_URL,
    SearchPageSelectors,
)
from cg_rera_extractor.browser.session import PlaywrightBrowserSession
from cg_rera_extractor.config.models import AppConfig
from cg_rera_extractor.detail.fetcher import fetch_and_save_details
from cg_rera_extractor.listing.models import ListingRecord
from cg_rera_extractor.listing.scraper import parse_listing_html
from cg_rera_extractor.parsing.mapper import map_raw_to_v1
from cg_rera_extractor.parsing.raw_extractor import extract_raw_from_html
from cg_rera_extractor.runs.status import RunStatus

LOGGER = logging.getLogger(__name__)
MAX_LISTINGS_PER_SEARCH = 50


def run_crawl(app_config: AppConfig) -> RunStatus:
    """Orchestrate a single crawl run using configured parameters."""

    run_config = app_config.run
    filters = run_config.search_filters
    run_id = _generate_run_id()
    started_at = datetime.now(timezone.utc)
    filters_used = {
        "districts": list(filters.districts),
        "statuses": list(filters.statuses),
        "project_types": list(filters.project_types or []),
    }

    counts = {
        "search_combinations_attempted": 0,
        "listings_parsed": 0,
        "details_fetched": 0,
        "projects_mapped": 0,
    }
    status = RunStatus(
        run_id=run_id,
        mode=str(run_config.mode.value if hasattr(run_config.mode, "value") else run_config.mode),
        started_at=started_at,
        filters_used=filters_used,
        counts=counts,
    )

    dirs = _prepare_run_directories(Path(run_config.output_base_dir).expanduser(), run_id)
    print(
        f"Starting run {run_id} in {status.mode} mode. Output folder: {dirs['run_dir']}"
    )
    LOGGER.info(
        "Starting run %s in %s mode. Output folder: %s", run_id, status.mode, dirs["run_dir"]
    )
    session: PlaywrightBrowserSession | None = None

    try:
        session = PlaywrightBrowserSession(app_config.browser)
        session.start()

        for district in filters.districts:
            for project_status in filters.statuses:
                counts["search_combinations_attempted"] += 1
                print(
                    f"Running search for district={district} status={project_status}"
                )
                LOGGER.info(
                    "Running search for district=%s status=%s", district, project_status
                )
                try:
                    _execute_search(
                        session,
                        district,
                        project_status,
                        filters.project_types,
                        SEARCH_PAGE_SELECTORS,
                    )
                    print("Waiting for manual CAPTCHA solve and search submission...")
                    wait_for_captcha_solved()
                    LOGGER.info(
                        "Waiting for results using selector %s", SEARCH_PAGE_SELECTORS.results_table
                    )
                    session.wait_for_selector(SEARCH_PAGE_SELECTORS.results_table, timeout_ms=20_000)
                    listings_html = session.get_page_html()
                    listings = parse_listing_html(listings_html, SEARCH_URL)

                    if len(listings) > MAX_LISTINGS_PER_SEARCH:
                        LOGGER.warning(
                            "Parsed %s listings; truncating to %s for safety",
                            len(listings),
                            MAX_LISTINGS_PER_SEARCH,
                        )
                        print(
                            f"Parsed {len(listings)} listings; truncating to {MAX_LISTINGS_PER_SEARCH}"
                        )
                        status.warnings.append(
                            f"Truncated listings for {district}/{project_status} to {MAX_LISTINGS_PER_SEARCH}"
                        )
                        listings = listings[:MAX_LISTINGS_PER_SEARCH]

                    for record in listings:
                        record.run_id = run_id
                    if not listings:
                        LOGGER.info("No listings found for %s / %s", district, project_status)
                        _save_listings_snapshot(
                            dirs["listings"], district, project_status, listings, listings_html
                        )
                        continue

                    counts["listings_parsed"] += len(listings)
                    LOGGER.info("Parsed %d listings for %s / %s", len(listings), district, project_status)
                    print(f"Parsed {len(listings)} listings for {district} / {project_status}")
                    _save_listings_snapshot(
                        dirs["listings"], district, project_status, listings, listings_html
                    )
                    fetch_and_save_details(session, listings, str(dirs["run_dir"]))
                    counts["details_fetched"] += len(listings)
                    LOGGER.info(
                        "Fetched %d detail pages for %s / %s",
                        len(listings),
                        district,
                        project_status,
                    )
                except Exception as exc:  # pragma: no cover - defensive logging
                    LOGGER.exception("Search failed for %s/%s", district, project_status)
                    print(f"Error during search for {district}/{project_status}: {exc}")
                    status.errors.append(str(exc))
    finally:
        if session is not None:
            session.close()

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


def _execute_search(
    session: PlaywrightBrowserSession,
    district: str,
    project_status: str,
    project_types: Iterable[str] | None,
    selectors: SearchPageSelectors,
) -> None:
    session.goto(SEARCH_URL)
    session.select_option(selectors.district_select, district)
    session.select_option(selectors.status_select, project_status)
    if project_types:
        session.select_option(selectors.project_type_select, list(project_types))


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
            v1_path = dirs["scraped_json"] / f"{html_file.stem}.v1.json"
            _write_json(
                v1_path,
                v1_project.model_dump(mode="json", exclude_none=True),
            )
            counts["projects_mapped"] += 1
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.exception("Failed to process %s", html_file)
            status.errors.append(str(exc))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = ["run_crawl"]
