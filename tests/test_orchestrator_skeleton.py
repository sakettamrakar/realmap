from __future__ import annotations

import json
from pathlib import Path

from cg_rera_extractor.config.models import (
    AppConfig,
    BrowserConfig,
    DatabaseConfig,
    RunConfig,
    RunMode,
    SearchFilterConfig,
)
from cg_rera_extractor.listing.models import ListingRecord
from cg_rera_extractor.parsing.schema import (
    RawExtractedProject,
    V1Metadata,
    V1Project,
    V1ProjectDetails,
    V1RawData,
)
from cg_rera_extractor.runs import orchestrator


def test_run_crawl_creates_outputs_and_counts(monkeypatch, tmp_path: Path) -> None:
    filters = SearchFilterConfig(districts=["Raipur"], statuses=["Registered"])
    run_config = RunConfig(
        mode=RunMode.FULL,
        search_filters=filters,
        output_base_dir=str(tmp_path),
        state_code="CG",
    )
    browser_config = BrowserConfig(driver="playwright", headless=True)
    app_config = AppConfig(
        run=run_config,
        browser=browser_config,
        db=DatabaseConfig(url="sqlite+pysqlite:///:memory:"),
    )

    fake_listing = ListingRecord(
        reg_no="CG-REG-001",
        project_name="Test Project",
        detail_url="https://example.com/details",
    )

    class FakeSession:
        def __init__(self, _config) -> None:
            self._html_counter = 0

        def start(self) -> None:  # pragma: no cover - no-op
            return None

        def goto(self, _url: str) -> None:  # pragma: no cover - no-op
            return None

        def fill(self, *_args, **_kwargs) -> None:  # pragma: no cover - no-op
            return None

        def select_option(self, *_args, **_kwargs) -> None:  # pragma: no cover - no-op
            return None

        def click(self, *_args, **_kwargs) -> None:  # pragma: no cover - no-op
            return None

        def wait_for_selector(self, *_args, **_kwargs) -> None:  # pragma: no cover - no-op
            return None

        def get_page_html(self) -> str:
            self._html_counter += 1
            return f"<html><body>page {self._html_counter}</body></html>"

        def close(self) -> None:  # pragma: no cover - no-op
            return None

    def fake_parse_listing_html(_html: str, _base_url: str) -> list[ListingRecord]:
        return [
            ListingRecord(
                reg_no=fake_listing.reg_no,
                project_name=fake_listing.project_name,
                detail_url=fake_listing.detail_url,
            )
        ]

    def fake_fetch_and_save_details(_session, listings: list[ListingRecord], output_base: str) -> None:
        for listing in listings:
            html_path = Path(output_base) / "raw_html" / f"project_{listing.reg_no}.html"
            html_path.parent.mkdir(parents=True, exist_ok=True)
            html_path.write_text("<html><label>Project Name</label><span>Demo</span></html>", encoding="utf-8")

    def fake_extract_raw_from_html(html: str, source_file: str) -> RawExtractedProject:
        return RawExtractedProject(
            source_file=source_file,
            registration_number="CG-REG-001",
            project_name="Test Project",
            sections=[],
        )

    def fake_map_raw_to_v1(raw: RawExtractedProject, state_code: str):  # type: ignore[override]
        return V1Project(
            metadata=V1Metadata(state_code=state_code),
            project_details=V1ProjectDetails(
                registration_number=raw.registration_number,
                project_name=raw.project_name,
                project_status="Registered",
                district="Raipur",
            ),
            promoter_details=[],
            land_details=[],
            building_details=[],
            unit_types=[],
            bank_details=[],
            documents=[],
            quarterly_updates=[],
            raw_data=V1RawData(),
        )

    monkeypatch.setattr(orchestrator, "PlaywrightBrowserSession", FakeSession)
    monkeypatch.setattr(orchestrator, "wait_for_captcha_solved", lambda: None)
    monkeypatch.setattr(orchestrator, "parse_listing_html", fake_parse_listing_html)
    monkeypatch.setattr(orchestrator, "fetch_and_save_details", fake_fetch_and_save_details)
    monkeypatch.setattr(orchestrator, "extract_raw_from_html", fake_extract_raw_from_html)
    monkeypatch.setattr(orchestrator, "map_raw_to_v1", fake_map_raw_to_v1)

    status = orchestrator.run_crawl(app_config)

    assert status.counts["search_combinations_attempted"] == 1
    assert status.counts["listings_parsed"] == 1
    assert status.counts["details_fetched"] == 1
    assert status.counts["projects_mapped"] == 1
    assert not status.errors

    run_dir = Path(run_config.output_base_dir) / "runs" / f"run_{status.run_id}"
    raw_html_dir = run_dir / "raw_html"
    raw_extracted_dir = run_dir / "raw_extracted"
    scraped_json_dir = run_dir / "scraped_json"
    listings_dir = run_dir / "listings"
    run_report = run_dir / "run_report.json"

    assert raw_html_dir.exists()
    assert raw_extracted_dir.exists()
    assert scraped_json_dir.exists()
    assert listings_dir.exists()
    assert run_report.exists()

    raw_files = list(raw_extracted_dir.glob("*.json"))
    v1_files = list(scraped_json_dir.glob("*.json"))
    assert raw_files, "Expected raw extracted JSON files to be written"
    assert v1_files, "Expected V1 JSON files to be written"
    assert any(path.name.endswith(".v1.json") for path in v1_files)
    listing_files = list(listings_dir.glob("*.json"))
    assert listing_files, "Expected listing snapshots to be written"

    with v1_files[0].open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    assert payload["project_details"]["registration_number"] == "CG-REG-001"
