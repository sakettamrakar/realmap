ARCHIVED - superseded by README.md and docs/DEV_GUIDE.md.

# Browser Closure Fix - Error Handling Improvements

## Problem
Browser was closing after page loading/CAPTCHA because exceptions during detail fetching were not being handled gracefully. The finally block in the orchestrator was closing the session even for transient errors.

## Root Cause
1. `fetch_and_save_details()` could throw exceptions during:
   - JavaScript detail link clicking
   - Page content retrieval with retries
   - Navigation back to listing page
   - Preview capture operations

2. These exceptions were not caught in the orchestrator loop, causing the finally block to close the entire browser session

3. Browser closure prevented completing the run even when some listings were successfully processed

## Solutions Implemented

### 1. Enhanced Orchestrator Error Handling (orchestrator.py)
**Before**: Detail fetching errors crashed the entire search combination
**After**: Wrapped detail fetch in try-except, logs error, continues processing

```python
try:
    fetch_and_save_details(...)
    counts["details_fetched"] += len(listings)
except Exception as exc:
    LOGGER.exception("Detail fetching failed for %s/%s: %s", ...)
    print(f"Warning: Detail fetching failed: {exc}")
    status.errors.append(f"Detail fetch failed...")
    # Continue processing instead of closing browser
```

### 2. Per-Listing Error Handling (fetcher.py)
**Before**: Single listing failure could crash the entire detail fetch loop
**After**: Each listing wrapped in try-except, continues on error

```python
for idx, record in enumerate(listings, 1):
    try:
        # Detail fetch logic for single listing
        ...
    except Exception as exc:
        LOGGER.exception("Failed to fetch details for %s", record.reg_no)
        print(f"Skipping {record.reg_no} - error fetching details: {exc}")
        continue  # Process next listing
```

### 3. Specific Exception Handling
**Preview Capture**: Already had try-except (kept as is)
**Navigation Back**: Already had try-except for go_back failures (kept as is)
**Main Detail Fetch**: Now caught with specific logging

## Benefits

✅ Browser stays open if one detail fetch fails
✅ Partial runs complete even with some failed details
✅ Clear error logging for debugging failures
✅ Graceful degradation instead of complete failure
✅ Runs can continue processing listings after transient errors

## Testing the Fix

To test the improved error handling:

```bash
# Run crawl with improved resilience
python -m cg_rera_extractor.cli --config config.realcrawl-2projects.yaml --mode full

# Then load and verify
python tools/load_runs_to_db.py --latest
python tools/check_db_counts.py
```

## Expected Behavior

- Browser stays open through entire crawl
- If detail fetch fails for one project, continues with others
- All successful details saved to run directory
- Errors logged but don't prevent completion
- Partial results available in scraped_json/

## Files Modified

1. `cg_rera_extractor/runs/orchestrator.py` - Wrapped detail fetch in try-except
2. `cg_rera_extractor/detail/fetcher.py` - Added per-listing try-except

## Backward Compatibility

✅ No breaking changes
✅ All existing functionality preserved
✅ Only adds resilience to error cases
✅ Error logging enhanced for visibility

