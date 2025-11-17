from pathlib import Path

from cg_rera_extractor.browser.search_page_config import SearchPageSelectors
from cg_rera_extractor.listing.scraper import parse_listing_html


def test_parse_real_listing_fixture_extracts_rows_and_links():
    html = Path("tests/fixtures/approved_project_list_sample.html").read_text(encoding="utf-8")
    selectors = SearchPageSelectors()

    listings = parse_listing_html(
        html,
        base_url="https://rera.cgstate.gov.in/Approved_project_List.aspx",
        listing_selector=selectors.listing_table,
        row_selector=selectors.row_selector,
        view_details_selector=selectors.view_details_link,
    )

    assert len(listings) == 3
    assert listings[0].project_name == "Sunshine Residency"
    assert listings[0].reg_no == "CG-RERA-PRJ-12345"
    assert listings[0].detail_url.endswith("CG-RERA-PRJ-12345")
    assert listings[0].row_index == 1
    assert listings[2].district == "Bilaspur"
    assert listings[2].detail_url.endswith("CG-RERA-PRJ-13579")
