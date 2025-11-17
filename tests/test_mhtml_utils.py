from pathlib import Path

from bs4 import BeautifulSoup

from cg_rera_extractor.parsing.mhtml_utils import extract_html_from_mhtml


def test_extract_html_from_mhtml_exposes_listing_table():
    html = extract_html_from_mhtml(Path("data/Real Estate Regulatory Authority.mhtml"))
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", id="ContentPlaceHolder1_gv_ProjectList")
    district_select = soup.find("select", id="ContentPlaceHolder1_District_Name")

    assert table is not None
    assert district_select is not None
