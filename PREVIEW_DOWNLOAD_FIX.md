# Preview Download Fix - Implementation Summary

## Changes Applied

### 1. **HTTP Fallback Support** (`preview_capture.py`)

Added `requests` library import with graceful fallback:
```python
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
```

### 2. **New HTTP Fallback Function**

Created `_try_http_fallback()` function that:
- Resolves relative URLs using `urljoin(base_url, url)`
- Makes direct HTTP requests with 30s timeout
- Verifies file size > 0
- Generates proper filenames from `field_key`
- Logs success/failure clearly
- Updates artifact with download results

### 3. **Improved `_download_url()` Function**

Enhanced with:
- **Increased timeout**: 10s → 30s for slow PDFs
- **Response validation**: Checks status 200, non-empty body
- **File verification**: Confirms file exists and size > 0
- **Better logging**: `[DOWNLOAD]`, `[DOWNLOAD_OK]`, `[DOWNLOAD_FAIL]` prefixes
- **Filename from field_key**: Uses `artifact.field_key` instead of generic `preview_0.pdf`
- **HTTP fallback**: Calls `_try_http_fallback()` if Playwright fails

### 4. **Improved Preview Processors**

Updated `_process_url_preview()` and `_process_click_preview()`:
- Capture actual URL after redirects: `artifact.source_url = new_page.url`
- Better error logging
- Call HTTP fallback on exception

## Testing

Run test script to verify PDFs downloaded:
```powershell
python test_preview_download.py
```

Expected output:
```
Checking: outputs/raipur-20/runs/run_XXXXX/previews
  ❌ CG_PCGRERA250518000012: EMPTY  # Old run
  
⚠️  NO PDFs FOUND - Need to re-run scraper with fixed code
```

## Next Steps

1. **Install requests library** (if not already):
   ```powershell
   pip install requests
   ```

2. **Re-run scraper** on one project to test:
   ```powershell
   python run_loader.py --config config.test-1project.yaml
   ```

3. **Verify PDFs downloaded**:
   ```powershell
   python test_preview_download.py
   ```

4. **Check PDF mapping**:
   - PDFs should be named by `field_key` (e.g., `BUILDING_PLAN.pdf`, `LAYOUT_PLAN.pdf`)
   - `metadata.json` should show `artifact_type: "pdf"` and file sizes

## Key Improvements

| Before | After |
|--------|-------|
| Silent download failures | Explicit error logging |
| Generic filenames (`preview_0.pdf`) | Meaningful names (`BUILDING_PLAN.pdf`) |
| 10s timeout | 30s timeout |
| No fallback | HTTP fallback on failure |
| No verification | File exists + size checks |
| Empty preview folders | PDFs actually saved |

## Expected Behavior

When scraper encounters preview button/URL:
1. Try Playwright `context.request.get()` with 30s timeout
2. Validate response: status 200, non-empty body
3. Write file with field_key-based name
4. Verify file exists and size > 0
5. If any step fails → try HTTP fallback with `requests`
6. If both fail → log error in artifact.notes

Result: **PDFs physically saved to disk with proper names and mapping**
