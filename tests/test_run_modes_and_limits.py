from __future__ import annotations

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


def test_run_crawl_dry_run_reports_pairs(monkeypatch, capsys):
    filters = SearchFilterConfig(districts=["Raipur", "Bilaspur"], statuses=["Registered"])
    run_config = RunConfig(
        mode=RunMode.DRY_RUN,
        search_filters=filters,
        output_base_dir="/tmp/unused",
        state_code="CG",
        max_search_combinations=1,
        max_total_listings=5,
    )
    app_config = AppConfig(
        run=run_config,
        browser=BrowserConfig(),
        db=DatabaseConfig(url="sqlite+pysqlite:///:memory:"),
    )

    def fail_session(_config):  # pragma: no cover - defensive stub
        raise AssertionError("Browser session should not start in DRY_RUN mode")

    monkeypatch.setattr(orchestrator, "PlaywrightBrowserSession", fail_session)

    status = orchestrator.run_crawl(app_config)

    captured = capsys.readouterr().out
    assert "DRY RUN" in captured
    assert "district=Raipur, status=Registered" in captured
    assert "Global listing cap: 5" in captured
    assert status.counts["search_combinations_planned"] == 1
    assert status.counts["search_combinations_processed"] == 0
    assert status.counts["listings_scraped"] == 0


def test_run_crawl_stops_after_combination_cap(monkeypatch, tmp_path: Path):
    filters = SearchFilterConfig(
        districts=["Raipur", "Bilaspur"],
        statuses=["Registered", "Ongoing"],
    )
    run_config = RunConfig(
        mode=RunMode.LISTINGS_ONLY,
        search_filters=filters,
        output_base_dir=str(tmp_path),
        state_code="CG",
        max_search_combinations=2,
        max_total_listings=None,
    )
    app_config = AppConfig(
        run=run_config,
        browser=BrowserConfig(),
        db=DatabaseConfig(url="sqlite+pysqlite:///:memory:"),
    )

    executed: list[tuple[str, str]] = []

    class FakeSession:
        def start(self):
            return None

        def goto(self, _url: str):  # pragma: no cover - no-op
            return None

        def select_option(self, *_args, **_kwargs):  # pragma: no cover - no-op
            return None

        def click(self, *_args, **_kwargs):  # pragma: no cover - no-op
            return None

        def wait_for_selector(self, *_args, **_kwargs):  # pragma: no cover - no-op
            return None

        def get_page_html(self) -> str:
            return "<html></html>"

        def close(self):  # pragma: no cover - no-op
            return None

    def record_search(
        _session,
        _search_url: str,
        _selectors,
        district: str,
        project_status: str,
        _project_types,
        is_first_search: bool = True,
    ):
        executed.append((district, project_status))
        return "<html></html>"

    monkeypatch.setattr(orchestrator, "PlaywrightBrowserSession", lambda _cfg: FakeSession())
    monkeypatch.setattr(orchestrator, "wait_for_captcha_solved", lambda: None)
    monkeypatch.setattr(orchestrator, "_run_search_and_get_listings", record_search)
    monkeypatch.setattr(
        orchestrator, "parse_listing_html", lambda _html, _url, **_kwargs: []
    )

    status = orchestrator.run_crawl(app_config)

    assert executed == [("Raipur", "Registered"), ("Raipur", "Ongoing")]
    assert status.counts["search_combinations_planned"] == 2
    assert status.counts["search_combinations_processed"] == 2
    assert status.counts["listings_scraped"] == 0


def test_run_crawl_honors_total_listing_limit(monkeypatch, tmp_path: Path):
    filters = SearchFilterConfig(
        districts=["Raipur"],
        statuses=["Registered", "Ongoing"],
    )
    run_config = RunConfig(
        mode=RunMode.FULL,
        search_filters=filters,
        output_base_dir=str(tmp_path),
        state_code="CG",
        max_search_combinations=None,
        max_total_listings=3,
    )
    app_config = AppConfig(
        run=run_config,
        browser=BrowserConfig(),
        db=DatabaseConfig(url="sqlite+pysqlite:///:memory:"),
    )

    class FakeSession:
        def __init__(self) -> None:
            self._counter = 0

        def start(self):  # pragma: no cover - no-op
            return None

        def goto(self, _url: str):  # pragma: no cover - no-op
            return None

        def select_option(self, *_args, **_kwargs):  # pragma: no cover - no-op
            return None

        def click(self, *_args, **_kwargs):  # pragma: no cover - no-op
            return None

        def wait_for_selector(self, *_args, **_kwargs):  # pragma: no cover - no-op
            return None

        def get_page_html(self) -> str:
            self._counter += 1
            return f"<html>batch {self._counter}</html>"

        def close(self):  # pragma: no cover - no-op
            return None

    listing_counter = 0

    def fake_parse_listing_html(_html: str, _url: str, **_kwargs):
        nonlocal listing_counter
        listing_counter += 1
        return [
            ListingRecord(
                reg_no=f"REG-{listing_counter}-{idx}",
                project_name=f"Project {listing_counter}-{idx}",
                detail_url=f"https://example.com/{listing_counter}/{idx}",
            )
            for idx in range(5)
        ]

    def fake_fetch_and_save_details(
        _session,
        _selectors,
        listings: list[ListingRecord],
        output_base: str,
        _listing_url: str,
        _state_code: str,
    ) -> None:
        raw_dir = Path(output_base) / "raw_html"
        raw_dir.mkdir(parents=True, exist_ok=True)
        for listing in listings:
            path = raw_dir / f"project_{listing.reg_no}.html"
            path.write_text("<html><label>Project Name</label><span>Demo</span></html>", encoding="utf-8")

    def fake_extract_raw_from_html(html: str, source_file: str) -> RawExtractedProject:
        return RawExtractedProject(
            source_file=source_file,
            registration_number=Path(source_file).stem.replace("project_", ""),
            project_name="Demo",
            sections=[],
        )

    def fake_map_raw_to_v1(raw: RawExtractedProject, state_code: str):  # type: ignore[override]
        return V1Project(
            metadata=V1Metadata(state_code=state_code),
            project_details=V1ProjectDetails(
                registration_number=raw.registration_number,
                project_status="Registered",
                district="Raipur",
            ),
            raw_data=V1RawData(),
        )

    monkeypatch.setattr(orchestrator, "PlaywrightBrowserSession", lambda _cfg: FakeSession())
    monkeypatch.setattr(orchestrator, "wait_for_captcha_solved", lambda: None)
    monkeypatch.setattr(orchestrator, "parse_listing_html", fake_parse_listing_html)
    monkeypatch.setattr(orchestrator, "fetch_and_save_details", fake_fetch_and_save_details)
    monkeypatch.setattr(orchestrator, "extract_raw_from_html", fake_extract_raw_from_html)
    monkeypatch.setattr(orchestrator, "map_raw_to_v1", fake_map_raw_to_v1)

    status = orchestrator.run_crawl(app_config)

    assert status.counts["listings_scraped"] == 3
    assert status.counts["details_fetched"] == 3
    assert status.counts["projects_parsed"] == 3
    assert status.counts["search_combinations_processed"] == 1

    run_dir = Path(run_config.output_base_dir) / "runs" / f"run_{status.run_id}"
    raw_html_files = list((run_dir / "raw_html").glob("*.html"))
    assert len(raw_html_files) == 3
