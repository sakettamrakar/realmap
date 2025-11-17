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

    def go_back(self) -> None:  # pragma: no cover - unused in this test
        return None

    def wait_for_selector(self, _selector: str, *_args, **_kwargs) -> None:  # pragma: no cover - unused
        return None

    def get_page_html(self) -> str:
        assert self._current_url is not None
        return self.html_by_url[self._current_url]


@dataclass
class JsDetailBrowserSession:
    listing_url: str
    html_by_url: dict[str, str]

    def __post_init__(self) -> None:
        self._current_url = self.listing_url
        self.clicked_selectors: list[str] = []
        self.go_back_calls: int = 0
        self.waited_for: list[str] = []

    def goto(self, url: str) -> None:  # pragma: no cover - not exercised in this test
        self._current_url = url

    def click(self, selector: str) -> None:
        self.clicked_selectors.append(selector)
        self._current_url = "detail"

    def go_back(self) -> None:
        self.go_back_calls += 1
        self._current_url = self.listing_url

    def wait_for_selector(self, selector: str, *_args, **_kwargs) -> None:
        self.waited_for.append(selector)

    def get_page_html(self) -> str:
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
        session,
        selectors,
        listings,
        str(tmp_path),
        "https://example.com/listings",
        "CG",
    )

    expected_a = tmp_path / "raw_html" / "project_CG_CG_01.html"
    expected_b = tmp_path / "raw_html" / "project_CG_CG_02.html"
    assert expected_a.read_text(encoding="utf-8") == "<html>A</html>"
    assert expected_b.read_text(encoding="utf-8") == "<html>B</html>"
    assert session.visited == ["https://example.com/a", "https://example.com/b"]


def test_fetch_and_save_details_uses_history_back_for_js_links(tmp_path):
    listing_url = "https://example.com/listings"
    html_by_url = {
        listing_url: "<html>Listings</html>",
        "detail": "<html>Detail</html>",
    }
    session = JsDetailBrowserSession(listing_url, html_by_url)
    listing = make_listing("CG-03", "javascript:__doPostBack('view','')")
    listing.row_index = 2

    selectors = SearchPageSelectors()
    fetch_and_save_details(
        session,
        selectors,
        [listing],
        str(tmp_path),
        listing_url,
        "CG",
    )

    expected_detail = tmp_path / "raw_html" / "project_CG_CG_03.html"
    assert expected_detail.read_text(encoding="utf-8") == "<html>Detail</html>"
    assert session.clicked_selectors == [
        "#ContentPlaceHolder1_gv_ProjectList > tbody > tr:nth-of-type(2) "
        "a[id*='gv_ProjectList_lnk_View']"
    ]
    assert session.go_back_calls == 1
    assert selectors.listing_table in session.waited_for

