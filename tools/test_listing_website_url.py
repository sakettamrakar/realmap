#!/usr/bin/env python
"""Test listing scraper website URL extraction."""

from pathlib import Path
from cg_rera_extractor.listing.scraper import parse_listing_html


def main():
    # Test on saved list page HTML
    html_path = Path("data/Real Estate Regulatory Authority2.htm")
    
    if not html_path.exists():
        print(f"HTML file not found: {html_path}")
        return
    
    html = html_path.read_text(encoding="utf-8")
    
    # Parse listings
    base_url = "https://rera.cgstate.gov.in/"
    listings = parse_listing_html(html, base_url)
    
    print(f"Found {len(listings)} listings")
    print()
    
    for listing in listings[:5]:
        print(f"Reg No: {listing.reg_no}")
        print(f"Project: {listing.project_name}")
        print(f"District: {listing.district}")
        print(f"Detail URL: {listing.detail_url}")
        print(f"Website URL: {listing.website_url}")
        print()


if __name__ == "__main__":
    main()
