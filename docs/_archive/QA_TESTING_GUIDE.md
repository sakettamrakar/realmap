ARCHIVED - superseded by docs/QA_GUIDE.md.

# QA Smoke Testing Guide

This guide explains how to test the QA component that performs field-by-field comparison between downloaded HTML files and extracted JSON data.

## Overview

The smoke test workflow has **4 steps**:

1. **Fresh Crawl** - Downloads detail HTML files from RERA website
2. **Artifact Inspection** - Verifies that HTML and JSON files were created
3. **Preview Artifact Check** - Looks for preview screenshots
4. **Field-by-Field QA** - Compares HTML content with extracted JSON values

## Component Architecture

### Main Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `dev_fresh_run_and_qa.py` | `tools/` | Orchestrator script that runs all steps |
| `run_field_by_field_qa.py` | `tools/` | Executes QA comparison logic |
| `field_extractor.py` | `cg_rera_extractor/qa/` | Extracts label-value pairs from HTML |
| `field_by_field_compare.py` | `cg_rera_extractor/qa/` | Compares V1 JSON against HTML fields |

### Data Flow

```
HTML File (raw_html/) 
    ↓
[field_extractor] → Normalized label-value map
    ↓
[field_by_field_compare] ← V1 JSON (scraped_json/)
    ↓
FieldDiff Objects
    ↓
[Aggregated into QA Report]
    ↓
qa_fields_report.json + qa_fields_report.md
```

## Testing Methods

### Method 1: Full Smoke Test (Recommended)

Runs a complete crawl followed by QA:

```bash
# From workspace root
python -m tools.dev_fresh_run_and_qa --mode full --config config.debug.yaml
```

**What it does:**
1. Starts a fresh crawl using the debug config
2. Waits for all HTML files and JSON files to be created
3. Runs field-by-field QA
4. Generates HTML and JSON reports

**Output locations:**
- HTML/JSON: `outputs/runs/run_TIMESTAMP/raw_html/` and `scraped_json/`
- QA Report: `outputs/runs/run_TIMESTAMP/qa_fields/qa_fields_report.json`
- QA Summary: `outputs/runs/run_TIMESTAMP/qa_fields/qa_fields_report.md`

### Method 2: QA Only (Existing Run)

Test the QA logic on an existing run without crawling:

```bash
# Find your run ID (format: YYYYMMDD_HHMMSS)
python tools/run_field_by_field_qa.py --run-id 20251117_123456
```

**Options:**
```bash
# Limit to first 10 projects
python tools/run_field_by_field_qa.py --run-id 20251117_123456 --limit 10

# Test specific project
python tools/run_field_by_field_qa.py --run-id 20251117_123456 --project-key "some-project-key"
```

### Method 3: Unit Tests

Run the unit tests for QA components:

```bash
# Test field extraction from HTML
pytest tests/qa/test_field_extractor.py -v

# Test comparison logic
pytest tests/qa/test_field_by_field_compare.py -v

# Run all QA tests
pytest tests/qa/ -v
```

## Understanding QA Reports

### JSON Report Structure

```json
{
  "summary": {
    "run_id": "20251117_123456",
    "total_projects": 50,
    "total_fields": 450,  // 50 projects × 9 fields each
    "match": 400,
    "mismatch": 20,
    "missing_in_html": 15,
    "missing_in_json": 10,
    "preview_unchecked": 5
  },
  "projects": [
    {
      "project_key": "CG-REG-001",
      "diffs": [
        {
          "field_key": "project_details.registration_number",
          "json_value": "CG-REG-001",
          "html_value": "CG-REG-001",
          "status": "match",
          "notes": null
        },
        ...
      ]
    },
    ...
  ]
}
```

### Field Comparison Statuses

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| `match` | HTML and JSON values are identical (after normalization) | ✅ No action |
| `mismatch` | HTML and JSON values differ | 🔴 Investigate parser |
| `missing_in_html` | Field present in JSON but not in HTML | ⚠️ Check HTML structure |
| `missing_in_json` | Field present in HTML but not extracted to JSON | 🔴 Investigate parser |
| `preview_unchecked` | Field value is "Preview" button (requires user interaction) | ⚠️ Check preview capture |

### Markdown Report

The `qa_fields_report.md` provides a quick summary table:

```markdown
# Field-by-field QA Report

| Project | Mismatches | Missing in HTML | Missing in JSON | Preview |
| --- | --- | --- | --- | --- |
| CG-REG-001 | 2 | 0 | 1 | 0 |
| CG-REG-002 | 0 | 1 | 0 | 3 |
```

## Mapped Fields

The QA checks these 9 project fields:

1. **registration_number** - Project RERA registration ID
2. **project_name** - Official project name
3. **project_type** - Residential/Commercial/Mixed-use
4. **project_status** - Registered/Ongoing/Completed
5. **district** - Location district
6. **tehsil** - Location sub-district
7. **project_address** - Full address
8. **launch_date** - When construction started
9. **expected_completion_date** - Expected completion date

## Normalization Rules

Before comparison, both HTML and JSON values are normalized:

1. **Whitespace collapse**: Multiple spaces → single space
2. **Trim edges**: Remove leading/trailing whitespace
3. **Case-insensitive**: Uppercase and lowercase are treated as equal
4. **Special handling for "Preview"**: Marked as `preview_unchecked` status

Example:
```
JSON:   "  Raipur  "  →  "raipur"
HTML:   "RAIPUR"      →  "raipur"
Result: Match ✅
```

## Run Directory Structure

After a complete smoke test, inspect:

```
outputs/runs/run_YYYYMMDD_HHMMSS/
├── raw_html/                       # Downloaded HTML files
│   ├── project_CG-REG-001.html
│   ├── project_CG-REG-002.html
│   └── ...
├── scraped_json/                   # Extracted JSON files
│   ├── project_CG-REG-001.v1.json
│   ├── project_CG-REG-002.v1.json
│   └── ...
├── previews/                       # Preview screenshots (if enabled)
│   └── [project_keys]/
├── qa_fields/                      # QA reports
│   ├── qa_fields_report.json
│   └── qa_fields_report.md
└── [other run artifacts]
```

## Troubleshooting

### No HTML files found

**Error:** `No detail HTML files found in raw_html/`

**Causes:**
1. Crawl failed before detail fetching
2. Detail fetcher module has issues
3. Configuration points to wrong output directory

**Fix:**
- Check crawler logs: `logs/`
- Verify `config.debug.yaml` has correct `output_base_dir`
- Check if search page crawl succeeded first

### Mismatch spike

**Problem:** Sudden increase in mismatches between runs

**Causes:**
1. Parser changes broke extraction
2. HTML structure changed on RERA website
3. Normalization rules insufficient

**Fix:**
- Review recent parser changes
- Check HTML samples: `raw_html/project_*.html`
- Run individual project QA: `--project-key CG-REG-XXX`
- Update field extraction logic if needed

### Preview unchecked increasing

**Problem:** Too many "preview_unchecked" statuses

**Causes:**
1. Preview capture feature disabled
2. JavaScript-heavy fields not being populated
3. Timing issues during crawl

**Fix:**
- Enable preview capture in config
- Check if JS execution is enabled
- Review detail page structure

## Quick Testing Workflow

### Step 1: Verify Existing Run
```bash
python tools/run_field_by_field_qa.py --run-id $(Get latest from outputs/runs/)
```

### Step 2: Run Sample QA (10 projects)
```bash
python tools/run_field_by_field_qa.py --run-id [YOUR_RUN_ID] --limit 10
```

### Step 3: Review Report
```bash
# View JSON report
Get-Content outputs/runs/run_[YOUR_ID]/qa_fields/qa_fields_report.json

# View Markdown summary
Get-Content outputs/runs/run_[YOUR_ID]/qa_fields/qa_fields_report.md
```

### Step 4: Deep Dive on Failures
```bash
python tools/run_field_by_field_qa.py --run-id [YOUR_RUN_ID] --project-key "CG-REG-001"
```

## Performance Notes

- **Small run (1-5 projects)**: ~5-10 seconds
- **Medium run (20-50 projects)**: ~30-60 seconds
- **Large run (100+ projects)**: 2-5 minutes

QA is I/O bound (reading HTML/JSON files), so optimize by:
1. Using `--limit` for quick tests
2. Using `--project-key` for specific investigation
3. Running tests on fast storage (SSD)

## Integration with CI/CD

The smoke test can be integrated into CI pipelines:

```bash
python -m tools.dev_fresh_run_and_qa --mode listings-only --config config.example.yaml
echo "Exit code: $?"
```

Exit codes:
- `0` = Success (all steps completed)
- `1-255` = Failure (see stderr for details)

## Advanced: Custom QA Checks

To add new field comparisons:

1. Edit `FIELD_MAPPING` in `cg_rera_extractor/qa/field_by_field_compare.py`
2. Update tests in `tests/qa/test_field_by_field_compare.py`
3. Re-run QA with: `python tools/run_field_by_field_qa.py --run-id [YOUR_ID]`

Example:
```python
FIELD_MAPPING = {
    "project_details.registration_number": "registration_number",
    # Add new field
    "project_details.total_units": "total_units",  # New!
}
```

---

**Last Updated:** November 17, 2025
**Project:** CG RERA Extractor

