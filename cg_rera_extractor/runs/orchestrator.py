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
from cg_rera_extractor.browser.session import PlaywrightBrowserSession
from cg_rera_extractor.config.models import AppConfig
from cg_rera_extractor.detail.fetcher import fetch_and_save_details
from cg_rera_extractor.listing.models import ListingRecord
from cg_rera_extractor.listing.scraper import parse_listing_html
from cg_rera_extractor.parsing.mapper import map_raw_to_v1
from cg_rera_extractor.parsing.raw_extractor import extract_raw_from_html
from cg_rera_extractor.runs.status import RunStatus

LOGGER = logging.getLogger(__name__)
CG_RERA_SEARCH_URL = "https://rera.cgstate.gov.in/ProjectSearch"


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
        "listings_scraped": 0,
        "details_fetched": 0,
        "projects_parsed": 0,
    }
    status = RunStatus(
        run_id=run_id,
        mode=str(run_config.mode.value if hasattr(run_config.mode, "value") else run_config.mode),
        started_at=started_at,
        filters_used=filters_used,
        counts=counts,
    )

    dirs = _prepare_run_directories(Path(run_config.output_base_dir).expanduser(), run_id)
    session: PlaywrightBrowserSession | None = None

    try:
        session = PlaywrightBrowserSession(app_config.browser)
        session.start()

        for district in filters.districts:
            for project_status in filters.statuses:
                try:
                    LOGGER.info("Running search for district=%s status=%s", district, project_status)
                    _execute_search(session, district, project_status, filters.project_types)
                    wait_for_captcha_solved()
                    session.wait_for_selector("table", timeout_ms=20_000)
                    listings_html = session.get_page_html()
                    listings = parse_listing_html(listings_html, CG_RERA_SEARCH_URL)
                    for record in listings:
                        record.run_id = run_id
                    if not listings:
                        LOGGER.info("No listings found for %s / %s", district, project_status)
                        continue

                    counts["listings_scraped"] += len(listings)
                    _save_listings_snapshot(dirs["listings"], district, project_status, listings)
                    fetch_and_save_details(session, listings, str(dirs["run_dir"]))
                    counts["details_fetched"] += len(listings)
                except Exception as exc:  # pragma: no cover - defensive logging
                    LOGGER.exception("Search failed for %s/%s", district, project_status)
                    status.errors.append(str(exc))
    finally:
        if session is not None:
            session.close()

    _process_saved_html(dirs, run_config.state_code, counts, status)
    status.finished_at = datetime.now(timezone.utc)
    return status


def _generate_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return f"{timestamp}_{suffix}"


def _prepare_run_directories(base_dir: Path, run_id: str) -> dict[str, Path]:
    run_dir = (base_dir / f"run_{run_id}").resolve()
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
) -> None:
    session.goto(CG_RERA_SEARCH_URL)
    session.select_option("select[name='district']", district)
    session.select_option("select[name='status']", project_status)
    if project_types:
        session.select_option("select[name='project_type']", list(project_types))
    session.click("button[type='submit']")


def _save_listings_snapshot(
    listings_dir: Path,
    district: str,
    project_status: str,
    listings: list[ListingRecord],
) -> None:
    filename = (
        f"listings_{_sanitize_for_filename(district)}_"
        f"{_sanitize_for_filename(project_status)}.json"
    )
    payload = [asdict(record) for record in listings]
    _write_json(listings_dir / filename, payload)


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
            v1_path = dirs["scraped_json"] / f"{html_file.stem}_v1.json"
            _write_json(
                v1_path,
                v1_project.model_dump(mode="json", exclude_none=True),
            )
            counts["projects_parsed"] += 1
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.exception("Failed to process %s", html_file)
            status.errors.append(str(exc))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = ["run_crawl"]
