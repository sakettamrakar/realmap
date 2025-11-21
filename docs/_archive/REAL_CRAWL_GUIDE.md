ARCHIVED - superseded by README.md and docs/DEV_GUIDE.md.

# Real Crawl Guide - Updated with Browser Resilience

## Prerequisites

1. Self-check passes: `python tools/self_check.py`
2. Postgres running with realmapdb database
3. Browser configured (Playwright installed)

## Running a Real FULL Crawl for 2 Projects

### Step 1: Start the Crawl

```bash
python -m cg_rera_extractor.cli --config config.realcrawl-2projects.yaml --mode full
```

This will:
- Launch browser in non-headless mode (you'll see it)
- Navigate to CG RERA portal
- Apply filters (Raipur district, Registered status)
- Click Search button
- **Pause waiting for CAPTCHA**: Solve CAPTCHA manually in browser

### Step 2: Solve CAPTCHA

When you see the message in terminal:
```
Solve CAPTCHA in the browser and click Search, then press ENTER here...
```

1. Look at the browser window
2. Solve the CAPTCHA puzzle
3. The results table should load automatically
4. Once you see the project listings, press ENTER in the terminal

### Step 3: Let It Fetch Details

The crawler will then:
- Fetch first project detail page (JavaScript click navigation)
- Extract raw HTML and data
- Save to `outputs/realcrawl/runs/run_*/raw_html/`
- Process data and extract fields
- Repeat for second project
- If any detail fetch fails, logs it and continues with next project

### Step 4: Wait for Completion

Terminal will show:
```
Run 20251120_XXXXXX_XXXXXX finished. Counts: {...}
```

### Step 5: Load Data into Database

```bash
python tools/load_runs_to_db.py --latest --verbose
```

This will:
- Load V1 JSON files from the run
- Show which projects are loaded
- If registration_number is empty, shows DEBUG message
- Displays summary of inserted records

### Step 6: Verify Counts

```bash
python tools/check_db_counts.py
```

This will show:
```
Database Row Counts
===================
Projects:           2
Promoters:          X
Buildings:          X
Unit Types:         X
Documents:          X
Quarterly Updates:  X
```

---

## Understanding the Output

### Success Indicators

✅ Browser stays open throughout (improved resilience)
✅ Listings are scraped: "Parsed X listings for..."
✅ Details are fetched: "[1/2] Fetching details..."
✅ HTML is saved: "Saved detail page for..."
✅ JSON is created: "Saved V1 project JSON..."
✅ Row counts > 0 after load

### Warnings to Expect

⚠️ "Timeout waiting for listing table after go_back" - Normal, recovers automatically
⚠️ "go_back() failed after fetching details" - OK, continues to next listing
⚠️ "Preview capture failed" - OK, still saves detail HTML and JSON

### Error Handling

- Listing parse failures: Skipped, process continues
- Detail fetch failures: Logged, next listing processed
- Navigation failures: Caught, recovers gracefully
- CAPTCHA timeout: Must manually retry the entire run

---

## Troubleshooting

### Browser closes immediately
- Check if CAPTCHA is visible in browser
- Try longer timeouts in config (increase slow_mo_ms)
- Check logs for specific error messages

### 0 projects upserted
- Check if registration_number is empty in JSON
- Use `--verbose` flag to see DEBUG messages
- Verify JSON files exist in outputs/realcrawl/runs/run_*/scraped_json/

### Table not found after CAPTCHA
- Increase wait timeout: Change `timeout_ms=20_000` to higher value
- Try manual filter fallback: Let browser do it manually

---

## File Locations

Run data: `outputs/realcrawl/runs/run_TIMESTAMP_HASH/`
- `raw_html/` - Downloaded HTML pages
- `raw_extracted/` - Parsed raw data (JSON)
- `scraped_json/` - V1 schema formatted JSON
- `listings/` - Parsed listings list
- `previews/` - Document preview captures

Database: `realmapdb` (Postgres localhost:5432)

---

## Quick Recap of Commands

```bash
# Self-check everything is working
python tools/self_check.py

# Run real FULL crawl for 2 projects (requires manual CAPTCHA)
python -m cg_rera_extractor.cli --config config.realcrawl-2projects.yaml --mode full

# Load V1 JSON into database
python tools/load_runs_to_db.py --latest --verbose

# Verify data in database
python tools/check_db_counts.py
```

---

## Notes

- First crawl of day requires manual CAPTCHA solving
- Subsequent runs may cache CAPTCHA state (browser-dependent)
- Detail fetching uses JavaScript navigation (ASP.NET postback)
- Navigation delays are intentional (8 second wait for postback)
- All errors are logged for debugging

The system now handles transient errors gracefully and won't close the browser on non-critical failures!

