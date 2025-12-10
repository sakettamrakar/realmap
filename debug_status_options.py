"""Debug script to list all status options."""

from cg_rera_extractor.browser.session import PlaywrightBrowserSession
from cg_rera_extractor.config.models import BrowserConfig
import time
import re

config = BrowserConfig(headless=False, default_timeout_ms=30000)
session = PlaywrightBrowserSession(config)

try:
    session.start()
    print("Navigating to RERA website...")
    session.goto("https://rera.cgstate.gov.in/Approved_project_List.aspx")
    time.sleep(5)
    
    html = session.get_page_html()
    
    # Extract ApplicantType select and its options
    print("\n=== ApplicantType (Status) options ===")
    select_match = re.search(
        r'<select[^>]*id="ContentPlaceHolder1_ApplicantType"[^>]*>.*?</select>',
        html,
        re.DOTALL
    )
    if select_match:
        select_html = select_match.group(0)
        options = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>', select_html)
        for value, label in options:
            print(f"  value={value}: {label}")
    
    print("\n=== District_Name options ===")
    select_match = re.search(
        r'<select[^>]*id="ContentPlaceHolder1_District_Name"[^>]*>.*?</select>',
        html,
        re.DOTALL
    )
    if select_match:
        select_html = select_match.group(0)
        options = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>', select_html)
        print(f"  Found {len(options)} districts:")
        for value, label in options[:15]:  # Show first 15
            print(f"    value={value}: {label}")
        if len(options) > 15:
            print(f"    ... and {len(options) - 15} more")
    
    print("\n(Browser is still open. Close it when done.)")
    time.sleep(3)
    
finally:
    try:
        session.close()
    except Exception:
        pass
