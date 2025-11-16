#!/usr/bin/env python3
"""Offline self-checks for the CG RERA extraction framework."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cg_rera_extractor.config.loader import load_config
from cg_rera_extractor.config.models import AppConfig, BrowserConfig, CrawlMode, RunConfig, SearchFilterConfig
from cg_rera_extractor.listing.models import ListingRecord
from cg_rera_extractor.listing.scraper import parse_listing_html
from cg_rera_extractor.parsing.mapper import map_raw_to_v1
from cg_rera_extractor.parsing.raw_extractor import extract_raw_from_html
from cg_rera_extractor.parsing.schema import RawExtractedProject
from cg_rera_extractor.runs import orchestrator
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"


@dataclass
class CheckResult:
    """Holds the outcome of a single self-check step."""

    name: str
    success: bool
    details: list[str] = field(default_factory=list)
    error: str | None = None


def run_check(name: str, func: Callable[[], list[str]]) -> CheckResult:
    """Execute a check and capture any errors."""

    try:
        details = func() or []
        return CheckResult(name=name, success=True, details=details)
    except Exception as exc:  # pragma: no cover - manual execution helper
        return CheckResult(name=name, success=False, error=str(exc))


def check_imports() -> list[str]:
    modules = [
        "cg_rera_extractor.config",
        "cg_rera_extractor.browser",
        "cg_rera_extractor.listing",
        "cg_rera_extractor.detail",
        "cg_rera_extractor.parsing",
        "cg_rera_extractor.runs",
    ]
    for module in modules:
        __import__(module)
    return [f"Imported {len(modules)} core packages successfully."]


def check_config_loader() -> list[str]:
    config_path = REPO_ROOT / "config.example.yaml"
    config = load_config(str(config_path))
    summary = (
        f"Mode={config.run.mode}, districts={config.run.search_filters.districts}, "
        f"statuses={config.run.search_filters.statuses}"
    )
    return ["Loaded config.example.yaml", summary]


def check_listing_parser() -> list[str]:
    fixture = FIXTURES_DIR / "listing_sample.html"
    html = fixture.read_text(encoding="utf-8")
    records = parse_listing_html(html, base_url="https://example.com/search")
    return [f"Parsed {len(records)} listing rows from fixture."]


def check_raw_extractor() -> list[str]:
    fixture = FIXTURES_DIR / "project_detail_sample.html"
    html = fixture.read_text(encoding="utf-8")
    raw = extract_raw_from_html(html, source_file=str(fixture))
    section_count = len(raw.sections)
    field_count = sum(len(section.fields) for section in raw.sections)
    return [f"Extracted {section_count} sections with {field_count} fields from detail fixture."]


def check_mapper() -> list[str]:
    fixture = FIXTURES_DIR / "raw_extracted_sample.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    raw = RawExtractedProject.model_validate(payload)
    project = map_raw_to_v1(raw, state_code="CG")
    name = project.project_details.project_name or "<missing>"
    reg_no = project.project_details.registration_number or "<missing>"
    return [f"Mapped raw sample to V1 schema: {name} ({reg_no})."]


def check_orchestrator_dry_run() -> list[str]:
    filters = SearchFilterConfig(districts=["Raipur"], statuses=["Registered"])
    run_config = RunConfig(
        mode=CrawlMode.FULL,
        search_filters=filters,
        output_base_dir=tempfile.mkdtemp(prefix="self_check_run_"),
        state_code="CG",
    )
    browser_config = BrowserConfig()
    app_config = AppConfig(run=run_config, browser=browser_config)

    listing = ListingRecord(
        reg_no="CG-TEST-001",
        project_name="Self Check Project",
        detail_url="https://example.com/detail/1",
    )
    detail_fixture = FIXTURES_DIR / "project_detail_sample.html"
    detail_html = detail_fixture.read_text(encoding="utf-8")

    class FakeSession:
        def __init__(self, *_args, **_kwargs) -> None:
            self.started = False

        def start(self) -> None:
            self.started = True

        def goto(self, _url: str) -> None:  # pragma: no cover - no-op
            return None

        def select_option(self, *_args, **_kwargs) -> None:  # pragma: no cover - no-op
            return None

        def click(self, *_args, **_kwargs) -> None:  # pragma: no cover - no-op
            return None

        def wait_for_selector(self, *_args, **_kwargs) -> None:  # pragma: no cover - no-op
            return None

        def get_page_html(self) -> str:
            return "<html></html>"

        def close(self) -> None:  # pragma: no cover - no-op
            return None

    fake_session = FakeSession()

    def fake_parse_listing_html(_html: str, _base_url: str) -> list[ListingRecord]:
        return [
            ListingRecord(
                reg_no=listing.reg_no,
                project_name=listing.project_name,
                detail_url=listing.detail_url,
            )
        ]

    def fake_fetch_and_save_details(_session, listings: list[ListingRecord], output_base: str) -> None:
        raw_dir = Path(output_base) / "raw_html"
        raw_dir.mkdir(parents=True, exist_ok=True)
        for item in listings:
            path = raw_dir / f"project_{item.reg_no}.html"
            path.write_text(detail_html, encoding="utf-8")

    from unittest import mock

    with ExitStack() as stack:
        stack.callback(lambda: shutil.rmtree(run_config.output_base_dir, ignore_errors=True))
        stack.enter_context(mock.patch.object(orchestrator, "PlaywrightBrowserSession", lambda _cfg: fake_session))
        stack.enter_context(mock.patch.object(orchestrator, "wait_for_captcha_solved", lambda: None))
        stack.enter_context(mock.patch.object(orchestrator, "parse_listing_html", fake_parse_listing_html))
        stack.enter_context(mock.patch.object(orchestrator, "fetch_and_save_details", fake_fetch_and_save_details))
        status = orchestrator.run_crawl(app_config)

    return [
        f"Orchestrator dry run completed (run_id={status.run_id})",
        f"Counts: {status.counts}",
    ]


def main() -> int:
    print("Realmap / CG RERA Extraction – Self Check")
    print("=" * 60)
    checks: List[CheckResult] = []

    check_functions: list[tuple[str, Callable[[], list[str]]]] = [
        ("Import health", check_imports),
        ("Config loader", check_config_loader),
        ("Listing parser", check_listing_parser),
        ("Raw extractor", check_raw_extractor),
        ("Mapper", check_mapper),
        ("Orchestrator dry run", check_orchestrator_dry_run),
    ]

    for name, func in check_functions:
        result = run_check(name, func)
        checks.append(result)
        status = "PASS" if result.success else "FAIL"
        print(f"[{status}] {name}")
        for line in result.details:
            print(f"    - {line}")
        if result.error:
            print(f"    ! {result.error}")

    passed = sum(1 for result in checks if result.success)
    total = len(checks)
    print("-" * 60)
    print(f"Summary: {passed}/{total} checks passed.")
    if passed != total:
        print("One or more checks failed. See details above.")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution entry point
    raise SystemExit(main())
