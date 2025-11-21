ARCHIVED - superseded by docs/QA_GUIDE.md.

# QA Testing Quick Start Guide

## Overview

You can test the QA smoke test functionality in three ways:

1. **Unit Tests** - Fast, test individual components
2. **Integration Tests** - Test complete workflow
3. **End-to-End Tests** - Run actual crawler + QA

---

## Quick Commands

### Run All QA Tests (Recommended First Step)

```powershell
# Run all QA unit tests
pytest tests/qa/ -v

# Run all QA integration tests
pytest tests/test_qa_smoke.py -v

# Run both
pytest tests/qa/ tests/test_qa_smoke.py -v
```

### Using the QA Helper Tool

The `tools/test_qa_helper.py` provides an interactive interface:

```powershell
# Run unit tests
python tools/test_qa_helper.py unit

# Run integration tests
python tools/test_qa_helper.py smoke

# List available runs
python tools/test_qa_helper.py list

# Inspect results from a run
python tools/test_qa_helper.py inspect run_20251117_123456

# Compare a specific project
python tools/test_qa_helper.py compare run_20251117_123456 CG-REG-001

# Run QA on existing run (limit to 10 projects for speed)
python tools/test_qa_helper.py qa run_20251117_123456 --limit 10

# Run fresh crawl + QA (takes 5-30 minutes)
python tools/test_qa_helper.py crawl
```

---

## Testing Scenarios

### Scenario 1: Quick Validation (5 minutes)

Test that QA components work correctly without running a full crawl:

```powershell
# Step 1: Run unit tests
pytest tests/qa/ -v

# Step 2: Run integration tests
pytest tests/test_qa_smoke.py -v

# Step 3: Inspect an existing run (if available)
python tools/test_qa_helper.py list
python tools/test_qa_helper.py inspect run_20251117_123456
```

**Expected output:**
- All unit tests pass ✅
- All integration tests pass ✅
- QA report shows stats for each project

---

### Scenario 2: Test with Existing Run Data (10 minutes)

Use data from a previous crawl run:

```powershell
# Step 1: List available runs
python tools/test_qa_helper.py list

# Step 2: Run QA on existing data (limit for speed)
python tools/test_qa_helper.py qa run_YYYYMMDD_HHMMSS --limit 10

# Step 3: Inspect results
python tools/test_qa_helper.py inspect run_YYYYMMDD_HHMMSS

# Step 4: Deep dive on specific project
python tools/test_qa_helper.py compare run_YYYYMMDD_HHMMSS CG-REG-001
```

**Output:**
- QA report for 10 projects
- Summary statistics (match rate, mismatches, etc.)
- Detailed field comparison for specific project

---

### Scenario 3: Full Smoke Test (20-30 minutes)

Run complete workflow: fresh crawl → QA validation:

```powershell
# Run with default debug config
python -m tools.dev_fresh_run_and_qa --mode full

# Or with custom config
python -m tools.dev_fresh_run_and_qa --config config.debug.yaml --mode listings-only
```

**What happens:**
1. Browser crawls RERA site and downloads HTML files
2. Parser extracts data to V1 JSON
3. QA compares HTML vs JSON field-by-field
4. Reports generated in `outputs/runs/run_YYYYMMDD_HHMMSS/qa_fields/`

---

## Understanding Test Results

### Unit Test Output

```
tests/qa/test_field_extractor.py::test_extract_label_value_map_handles_tables_and_preview PASSED
tests/qa/test_field_by_field_compare.py::test_compare_v1_to_html_fields_classifies_statuses PASSED
tests/test_qa_smoke.py::TestHTMLFieldExtraction::test_extracts_all_expected_fields PASSED
...
```

✅ **PASSED** = Test succeeded
❌ **FAILED** = Test failed (needs investigation)

### Integration Test Categories

The smoke tests verify:

1. **HTML Extraction** (8 tests)
   - Correctly parses HTML tables
   - Normalizes field labels
   - Handles Preview buttons

2. **JSON Parsing** (4 tests)
   - Valid V1 schema
   - All required fields present
   - Null handling

3. **Field Comparison** (7 tests)
   - Identifies matching fields
   - Detects mismatches
   - Marks missing fields
   - Handles Preview buttons

4. **Integration Workflow** (4 tests)
   - Full workflow runs without errors
   - Report structure is valid
   - Handles missing data gracefully
   - Handles extra data gracefully

5. **Edge Cases** (3 tests)
   - Whitespace normalization
   - Case-insensitive comparison
   - None and empty string handling

### QA Report Example

```
=== QA Results for Run: run_20251117_123456 ===

Summary Statistics:
  Total Projects:        25
  Total Fields:          225 (25 × 9 fields)
  Matches:               210
  Mismatches:            8
  Missing in HTML:       4
  Missing in JSON:       2
  Preview Unchecked:     1

Match Rate: 93.3%

Project-Level Breakdown:
  Project              Match      Mismatch   Missing HTML   Missing JSON
  -------              -----      --------   ------------   -----------
  CG-REG-001           9          0          0              0
  CG-REG-002           8          1          0              0
  CG-REG-003           7          0          1              1
  ...
```

---

## Field Comparison Details

When you run `python tools/test_qa_helper.py compare run_20251117_123456 CG-REG-001`, you see:

```
Field                                   Status               JSON Value           HTML Value
-------                                 ------               ----------           ----------
registration_number                     match                CG-REG-001           CG-REG-001
project_name                            match                Garden Villas        Garden Villas
project_type                            match                Residential          Residential
district                                match                Raipur               Raipur
tehsil                                  mismatch             Abhanpur             Tilda
project_status                          preview_unchecked    Ongoing              (Preview)
project_address                         match                123 Main St          123 Main St
launch_date                             missing_in_html      2023-01-15           (null)
expected_completion_date                missing_in_json      (null)               2024-12-31

Issues Details:
❌ MISMATCH: project_details.tehsil
   JSON:  Abhanpur
   HTML:  Tilda

❓ PREVIEW: project_details.project_status
   Requires user interaction (Preview button)

⚠️  MISSING IN HTML: project_details.launch_date
   JSON:  2023-01-15

⚠️  MISSING IN JSON: project_details.expected_completion_date
   HTML:  2024-12-31
```

---

## Troubleshooting

### Tests Fail to Import Modules

```
ModuleNotFoundError: No module named 'cg_rera_extractor'
```

**Fix:** Make sure you're in the workspace root:
```powershell
cd C:\GIT\realmap
```

### No Runs Available

```
No runs found in outputs/runs/
```

**Fix:** Either:
1. Run `python -m tools.dev_fresh_run_and_qa` to generate data
2. Ensure you're looking in the right directory

### QA Report Not Generated

**Causes:**
- Crawl didn't complete
- HTML/JSON files not in expected locations
- QA script encountered an error

**Fix:**
```powershell
# Check if HTML/JSON exist
Get-ChildItem outputs/runs/run_*/raw_html/
Get-ChildItem outputs/runs/run_*/scraped_json/

# Re-run QA explicitly
python tools/run_field_by_field_qa.py --run-id [YOUR_RUN_ID]
```

### High Mismatch Rate

If match rate drops significantly:

```powershell
# Check specific projects for common patterns
python tools/test_qa_helper.py compare [RUN_ID] CG-REG-001
python tools/test_qa_helper.py compare [RUN_ID] CG-REG-002

# Compare with previous run
python tools/test_qa_helper.py inspect [OLD_RUN_ID]
```

---

## Performance Tips

- **Unit tests**: ~5-10 seconds
- **Integration tests**: ~10-15 seconds  
- **QA on 10 projects**: ~15-20 seconds
- **QA on 100 projects**: ~60-90 seconds
- **Full crawl + QA**: 20-30 minutes (depends on number of listings)

**To speed up:**
```powershell
# Test only specific component
pytest tests/qa/test_field_extractor.py -v

# Run QA with project limit
python tools/test_qa_helper.py qa [RUN_ID] --limit 5

# Run crawl with limited listings (change config)
python -m tools.dev_fresh_run_and_qa --config config.debug.yaml --mode listings-only
```

---

## Advanced Usage

### Run Specific Test

```powershell
# Test only extraction
pytest tests/qa/test_field_extractor.py::test_extract_label_value_map_handles_tables_and_preview -v

# Test only comparison logic
pytest tests/qa/test_field_by_field_compare.py -v

# Test only integration
pytest tests/test_qa_smoke.py::TestQASmokeTestIntegration -v
```

### Run Tests with Coverage

```powershell
pytest tests/qa/ tests/test_qa_smoke.py --cov=cg_rera_extractor.qa --cov-report=html
# Open htmlcov/index.html in browser to see coverage
```

### Filter by Status Type

```powershell
# Only inspect mismatches
python tools/run_field_by_field_qa.py --run-id [RUN_ID] > qa_result.json
# Then grep/parse for "mismatch" status
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `tests/qa/test_field_extractor.py` | Tests HTML label extraction |
| `tests/qa/test_field_by_field_compare.py` | Tests comparison logic |
| `tests/test_qa_smoke.py` | Integration tests |
| `tools/test_qa_helper.py` | Interactive CLI helper |
| `tools/dev_fresh_run_and_qa.py` | Full smoke test orchestrator |
| `tools/run_field_by_field_qa.py` | QA engine |
| `cg_rera_extractor/qa/field_extractor.py` | HTML parsing logic |
| `cg_rera_extractor/qa/field_by_field_compare.py` | Comparison logic |

---

## Next Steps

1. **Start here:** `pytest tests/qa/ -v` (5 minutes)
2. **Then test integration:** `pytest tests/test_qa_smoke.py -v` (5 minutes)
3. **Inspect existing run:** `python tools/test_qa_helper.py list` and `inspect`
4. **Run full test:** `python -m tools.dev_fresh_run_and_qa` (20-30 minutes)

**Happy Testing! 🚀**

