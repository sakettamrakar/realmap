"""Debug script to inspect RERA website selectors."""

from cg_rera_extractor.browser.session import PlaywrightBrowserSession
from cg_rera_extractor.config.models import BrowserConfig
import time

config = BrowserConfig(headless=False, default_timeout_ms=30000)
session = PlaywrightBrowserSession(config)

try:
    session.start()
    print("Navigating to RERA website...")
    session.goto("https://rera.cgstate.gov.in/Approved_project_List.aspx")
    print("Page loaded. Waiting 5 seconds for any dynamic content...")
    time.sleep(5)
    
    html = session.get_page_html()
    
    # Look for select elements
    print("\n=== All <select> elements on page ===")
    import re
    selects = re.findall(r'<select[^>]*id="([^"]*)"[^>]*>.*?</select>', html, re.DOTALL)
    for select_id in selects[:10]:  # Limit to first 10
        print(f"  - {select_id}")
    
    # Look for status-related elements
    print("\n=== Looking for 'status' or 'applicant' elements ===")
    if 'ApplicantType' in html:
        print("  Found 'ApplicantType' in HTML")
        # Extract the surrounding context
        idx = html.find('ApplicantType')
        print(f"  Context: ...{html[max(0, idx-100):idx+200]}...")
    else:
        print("  'ApplicantType' NOT found in HTML")
    
    # Look for district elements
    print("\n=== Looking for district selector ===")
    if 'District_Name' in html:
        print("  Found 'District_Name' in HTML")
    else:
        print("  'District_Name' NOT found in HTML")
    
    print("\n=== Page title ===")
    title_match = re.search(r'<title>([^<]*)</title>', html)
    if title_match:
        print(f"  {title_match.group(1)}")
    
    print("\n(Browser is still open. Close it manually when done.)")
    
finally:
    try:
        session.close()
    except Exception:
        pass
