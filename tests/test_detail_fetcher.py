"""Tests for the detail page fetcher."""

from dataclasses import dataclass

from cg_rera_extractor.browser.search_page_config import SearchPageSelectors
from cg_rera_extractor.detail.fetcher import fetch_and_save_details
from cg_rera_extractor.listing.models import ListingRecord


@dataclass
class FakeBrowserSession:
    html_by_url: dict[str, str]

    def __post_init__(self) -> None:
        self.visited: list[str] = []
        self._current_url: str | None = None

    def goto(self, url: str) -> None:
        self.visited.append(url)
        self._current_url = url

    def click(self, _selector: str) -> None:  # pragma: no cover - unused in this test
        return None

    def wait_for_selector(self, _selector: str, *_args, **_kwargs) -> None:  # pragma: no cover - unused
        return None

    def get_page_html(self) -> str:
        assert self._current_url is not None
        return self.html_by_url[self._current_url]


def make_listing(reg_no: str, detail_url: str) -> ListingRecord:
    return ListingRecord(
        reg_no=reg_no,
        project_name="Project",
        promoter_name="Promoter",
        district="District",
        tehsil="Tehsil",
        status="Status",
        detail_url=detail_url,
        run_id="run-1",
    )


def test_fetch_and_save_details_persists_each_listing(tmp_path):
    html_by_url = {
        "https://example.com/a": "<html>A</html>",
        "https://example.com/b": "<html>B</html>",
    }
    session = FakeBrowserSession(html_by_url)
    listings = [
        make_listing("CG/01", "https://example.com/a"),
        make_listing("CG-02", "https://example.com/b"),
    ]

    selectors = SearchPageSelectors()
    fetch_and_save_details(
        session, selectors, listings, str(tmp_path), "https://example.com/listings"
    )

    expected_a = tmp_path / "raw_html" / "project_CG_01.html"
    expected_b = tmp_path / "raw_html" / "project_CG_02.html"
    assert expected_a.read_text(encoding="utf-8") == "<html>A</html>"
    assert expected_b.read_text(encoding="utf-8") == "<html>B</html>"
    assert session.visited == ["https://example.com/a", "https://example.com/b"]

