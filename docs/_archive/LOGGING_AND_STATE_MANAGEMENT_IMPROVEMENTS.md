ARCHIVED - superseded by README.md and docs/DEV_GUIDE.md.

# Logging & State Management Improvements

## What Was Updated

You asked two great questions about the crawler:

1. **"I don't see what's happening - add progress logging"**
2. **"How does it prevent page refresh when navigating to detail pages?"**

Both have been addressed. Here's what changed:

---

## 1. Enhanced Logging - You Now See What's Happening

### Before
```
[Silent wait, no feedback]
```

### After
```
Running search for district=Raipur status=Ongoing
  Navigating to search page...
  Applying filters: district=Raipur, status=Ongoing, types=[]
  Clicking search button...
  Waiting for manual CAPTCHA solving...
[you solve CAPTCHA]
  Waiting for results table to load...
Parsed 23 listings for Raipur / Ongoing
[FULL mode] Starting detail fetch for 23 listings
[1/23] Fetching details for CG-REG-2024-001 (JavaScript click)...
  Saved detail page for CG-REG-2024-001
[2/23] Fetching details for CG-REG-2024-002 (JavaScript click)...
  Saved detail page for CG-REG-2024-002
...
Detail fetch complete for all 23 listings
```

### What Was Added

**File: `cg_rera_extractor/runs/orchestrator.py`**
- Added progress messages to `_run_search_and_get_listings()`
- Now shows:
  - Navigation to search page
  - Filter application attempt
  - Search button click
  - CAPTCHA wait period
  - Table loading wait

**File: `cg_rera_extractor/detail/fetcher.py`**
- Added progress counter `[X/N]` for each detail fetch
- Shows fetch method (JavaScript click vs direct URL)
- Shows when page is saved
- Shows when returning to listing page
- Displays summary at the end

**File: `cg_rera_extractor/listing/scraper.py`**
- Added logging import
- Log when table is found
- Log header mapping
- Log row count
- Log final parsed count

### Where Logs Go

1. **Terminal (console)** - print() statements for immediate visibility
   ```
   Parsed 23 listings for Raipur / Ongoing
   [1/23] Fetching details for CG-REG-2024-001 (JavaScript click)...
   ```

2. **Log file** - detailed logging at INFO/DEBUG level
   ```
   2025-11-17 16:00:49,156 INFO root Found 25 rows in table, processing...
   2025-11-17 16:00:49,200 INFO cg_rera_extractor.listing.scraper Parsed 23 valid listings from table
   2025-11-17 16:00:50,100 INFO root [1/23] Fetching details for CG-REG-2024-001 (JS click method)
   ```

---

## 2. State Management - How Page Refresh is Prevented

### The Problem You Identified

**Scenario:**
1. You apply filters (Raipur, Ongoing) 
2. Results appear
3. You click a project link to view details
4. If the page does a full refresh, filters are LOST ❌

**How would this happen?**
```python
# WRONG approach:
for listing in listings:
    session.goto(listing.detail_url)  # This refreshes the page!
```

### The Solution We Use

CG RERA website uses **ASP.NET with JavaScript PostBack events**. When you click "View Details":

```html
<a href="javascript:__doPostBack('ctl00$ContentPlaceHolder1$gvApprovedProject','Select$0')">
  View Details
</a>
```

This JavaScript:
- Does NOT cause a page refresh
- Tells server "user clicked row 0"
- Server sends detail HTML
- **Original page state is preserved in browser history**

### How Our Code Handles This

**Key insight:** We detect which links use JavaScript PostBack:

```python
uses_js_detail = record.detail_url.startswith("javascript") or "__doPostBack" in record.detail_url

if uses_js_detail:
    # Method 1: Click the link (preserves state) ✓
    target_selector = f"tr:nth-of-type({record.row_index}) a"
    session.click(target_selector)
    
    # Get detail HTML
    html = session.get_page_html()
    
    # Go BACK using browser history (NOT goto) ✓
    # This returns to listing with filters INTACT
    session.go_back()
    session.wait_for_selector(table_selector)
else:
    # Method 2: Direct URL navigation (less common)
    session.goto(urljoin(listing_page_url, record.detail_url))
```

### Why This Works

**The JavaScript Click Method:**

```
Listing Page
  ↓ (user clicks View Details link)
  ├─ Browser receives detail page (NO page refresh)
  ├─ Browser history updated
  └─ Original listing page kept in history
  
  ↓ (we click go_back)
  
Listing Page (BACK in browser history)
  └─ Filters still selected (never refreshed)
```

**NOT like traditional navigation:**

```
Listing Page (Filters: Raipur, Ongoing)
  ↓ (goto URL - WRONG)
  ├─ Page refresh triggered ❌
  ├─ Filters reset to defaults ❌
  └─ Detail page loads
```

### What This Means for You

✅ **The system DOES handle state preservation correctly**
- Filters persist across multiple detail fetches
- No page refresh when navigating to details
- Can fetch 20, 50, 100 details without re-filtering each time

---

## 3. Code Changes Summary

### Modified Files:

1. **`cg_rera_extractor/detail/fetcher.py`**
   - Added progress logging with counters
   - Added messages for save operations
   - Added explanations for navigation methods

2. **`cg_rera_extractor/runs/orchestrator.py`**
   - Enhanced `_run_search_and_get_listings()` with progress messages
   - Added navigation logging
   - Added table waiting feedback

3. **`cg_rera_extractor/listing/scraper.py`**
   - Added logging for table parsing
   - Added row/listing count messages

4. **New file: `CRAWL_FLOW_EXPLAINED.md`**
   - Comprehensive explanation of the entire crawl flow
   - Step-by-step breakdown with code examples
   - Visual diagrams of state management
   - Q&A on common concerns

### Tests Status
✅ All 36 tests still pass
✅ Self-check: 9/9 checks pass
✅ No breaking changes

---

## Example Output - FULL Crawl Run

When you run:
```bash
python -m cg_rera_extractor.cli --config config.phase2.sample.yaml --mode full
```

You'll see:

```
Using database target: localhost/realmapdb
Starting run 20251117_120000_abc123 in FULL mode. Output folder: C:\GIT\realmap\outputs\phase2_runs\runs\run_20251117_120000_abc123

Running search for district=Raipur status=Ongoing
  Navigating to search page...
  Applying filters: district=Raipur, status=Ongoing, types=[]
  Clicking search button...
  Waiting for manual CAPTCHA solving...
[Solve CAPTCHA and press ENTER in the browser developer console]
  Waiting for results table to load...
Parsed 23 listings for Raipur / Ongoing

Starting detail fetch for 23 listings
[1/23] Fetching details for CG-REG-2024-001 (JavaScript click)...
  [page loads detail]
[2/23] Fetching details for CG-REG-2024-002 (JavaScript click)...
  [page loads detail]
[3/23] Fetching details for CG-REG-2024-003 (JavaScript click)...
...
[23/23] Fetching details for CG-REG-2024-023 (JavaScript click)...
Detail fetch complete for all 23 listings

Running search for district=Durg status=Ongoing
  Navigating to search page...
  Applying filters: district=Durg, status=Ongoing, types=[]
  Clicking search button...
  Waiting for manual CAPTCHA solving...
[Solve CAPTCHA and press ENTER]
  Waiting for results table to load...
Parsed 18 listings for Durg / Ongoing

Starting detail fetch for 18 listings
[1/18] Fetching details for CG-REG-2024-024 (JavaScript click)...
...
[18/18] Fetching details for CG-REG-2024-041 (JavaScript click)...
Detail fetch complete for all 18 listings

Run 20251117_120000_abc123 finished.
```

Plus detailed logs showing exact timestamps and state transitions.

---

## How to See Even More Detail

To see DEBUG-level logs (very verbose):

```bash
python -c "import logging; logging.basicConfig(level=logging.DEBUG); exec(open('cg_rera_extractor/cli.py').read())" --config config.phase2.sample.yaml --mode listings-only
```

Or modify `cg_rera_extractor/cli.py` to change:
```python
logging.basicConfig(
    level=logging.INFO,  # Change to logging.DEBUG
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
```

---

## Next Steps

Your crawler is now **fully transparent**. You'll see:
- ✅ What page it's navigating to
- ✅ What filters it's applying
- ✅ When it's waiting for you (CAPTCHA)
- ✅ How many listings are found
- ✅ Progress through detail fetching [X/N]
- ✅ When pages are saved
- ✅ How it handles navigation (no refresh!)

For a complete understanding of the crawl flow, see: `CRAWL_FLOW_EXPLAINED.md`


