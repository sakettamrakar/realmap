from pathlib import Path

from cg_rera_extractor.browser.search_page_config import SearchPageSelectors
from cg_rera_extractor.listing.scraper import parse_listing_html


def test_parse_real_listing_fixture_extracts_rows_and_links():
    html = Path("tests/fixtures/cg_rera_approved_list.html").read_text(encoding="utf-8")
    selectors = SearchPageSelectors()

    listings = parse_listing_html(
        html,
        base_url="https://rera.cgstate.gov.in/Approved_project_List.aspx",
        listing_selector=selectors.listing_table,
        row_selector=selectors.row_selector,
        view_details_selector=selectors.view_details_link,
    )

    assert len(listings) == 10
    assert listings[0].project_name == "SPARSH LIFE CITY"
    assert listings[0].reg_no == "PCGRERA160218000001"
    assert "__doPostBack" in listings[0].detail_url
    assert listings[0].row_index == 1
    assert listings[1].district == "RAIPUR"
    assert listings[0].detail_url.endswith("lnk_View','')")
