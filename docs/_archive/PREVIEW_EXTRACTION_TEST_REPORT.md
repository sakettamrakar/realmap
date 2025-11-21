ARCHIVED - superseded by README.md and docs/DEV_GUIDE.md.

# Full Crawler Test Report - Preview Button Extraction Feature

## Test Summary
**Date**: November 17, 2025  
**Test Run ID**: 20251117_142842_d3db76  
**Configuration**: FULL mode, 1 district (Raipur), 2 listings  
**Status**: ✅ CRAWL COMPLETED | ⚠️ PREVIEW EXTRACTION ISSUE FOUND

---

## System Health

### 1. System Checks
✅ **All 9 self-checks PASSED**
- Import health: OK
- Config loader: OK
- Listing parser: OK
- Raw extractor: OK
- Mapper: OK
- RunStatus schema: OK
- DB connection: OK
- Tiny loader: OK
- Orchestrator dry run: OK

### 2. Crawler Execution
✅ **FULL Mode Crawl Executed Successfully**
```
Run ID: 20251117_142842_d3db76
Mode: FULL
Duration: ~2-3 minutes
Output Directory: outputs/demo-run/runs/run_20251117_142842_d3db76/
```

**Counts:**
```
search_combinations_planned:  1
search_combinations_attempted: 1
search_combinations_processed: 1
listings_scraped:             2
listings_parsed:              2
details_fetched:              2
projects_parsed:              2
projects_mapped:              2
dq_warnings:                  4
```

### 3. Test Suite
⚠️ **37/38 tests PASSED**
- 1 pre-existing failure: `test_fake_browser_session_matches_protocol` (unrelated)
- All QA tests: ✅ PASSING
- All system integration tests: ✅ PASSING

---

## Preview Button Extraction Analysis

### ✅ Raw Extractor Working Correctly

**Preview Fields Detected**: 15 fields with preview buttons

**Examples:**
```
Segment Specific:
  - Registration Certificate
  - Bank Account PassBook Front Page
  - Fee Calculation Sheet

Land Documents:
  - Encumbrances on Land/Non-Encumbrances Certificate

Approval From Competent Authorities:
  - Approval Letter of Town And Country Planning
  - Sanctioned Layout Plan
  - Building Permission from local Authority

Project Specific:
  - Project Specifications
  - Apartment Details

Miscellaneous:
  - Development Team Details
  - Development Work Plan

Acts & Rules:
  - Affidavit Cum Declaration
  - Engineer Certificate
  - CA Certificate
```

**Status**: ✅ Raw extractor correctly marks `preview_present=True` and captures PDF/image URLs in `preview_hint`

### ❌ Mapper Not Building Preview Placeholders

**Issue**: The V1 mapper is NOT creating preview artifact entries for unmapped sections

**Root Cause** (in `cg_rera_extractor/parsing/mapper.py`, lines 98-103):
```python
# When a section is unmapped (not in logical_sections_and_keys.json):
for field in section.fields:
    if field.label:
        target[field.label] = field.value or ""  # ← Preview info LOST here!
    # ❌ NO CHECK for field.preview_present
```

**Contrast with mapped sections** (lines 111-118):
```python
# When a section IS mapped:
if canonical_key:
    logical_section_data[canonical_key] = field.value or ""
    if field.preview_present and canonical_key not in previews:
        previews[canonical_key] = PreviewArtifact(...)  # ✅ Preview captured!
```

**Impact**:
- Preview metadata (15 preview artifacts) = 0 entries in V1 output
- `previews` dict in V1 JSON is empty `{}`
- Preview capture phase has no placeholders to work with
- No preview files downloaded or stored

### ❌ Preview Capture Phase Not Executed

**Expected Behavior**: After building preview placeholders in mapper, preview capture phase should:
1. Click preview buttons
2. Handle popup windows or modal dialogs
3. Download PDF/image files
4. Save metadata to `previews/` directory

**Actual Behavior**: 
- Previews directory created but empty
- No preview files downloaded
- No preview metadata saved

---

## Output Structure

```
run_20251117_142842_d3db76/
├── listings/                          ✅
│   ├── listings_Raipur_Ongoing.html
│   └── listings_Raipur_Ongoing.json
├── raw_html/                          ✅
│   ├── project_CG_PCGRERA240218000002.html
│   └── project_CG_PCGRERA270418000009.html
├── raw_extracted/                     ✅
│   ├── project_CG_PCGRERA240218000002.json (15 preview fields detected)
│   └── project_CG_PCGRERA270418000009.json
├── scraped_json/                      ⚠️  PARTIAL
│   ├── project_CG_PCGRERA240218000002.v1.json (previews: {})
│   └── project_CG_PCGRERA270418000009.v1.json
├── previews/                          ❌ EMPTY
│   └── (no files)
└── run_report.json                    ✅
```

---

## Key Findings

| Component | Status | Evidence |
|-----------|--------|----------|
| HTML Page Fetch | ✅ Works | 2 detail pages fetched successfully |
| Listing Scrape | ✅ Works | 2 listings parsed from search results |
| Raw HTML Analysis | ✅ Works | Preview buttons found in HTML markup |
| Raw Extraction | ✅ Works | 15 preview_present=True fields detected |
| V1 Mapping | ❌ Bug | Preview fields in unmapped sections ignored |
| Preview Capture | ❌ Blocked | No preview placeholders to process |
| File Downloads | ❌ Blocked | No URLs captured in previews dict |

---

## Bug Details

### File: `cg_rera_extractor/parsing/mapper.py`

**Lines 98-103** (Unmapped Section Handling):
```python
if not logical_section:
    target = unmapped_sections.setdefault(section.section_title_raw, {})
    for field in section.fields:
        if field.label:
            target[field.label] = field.value or ""  # ❌ Losing preview info
    continue
```

**Lines 111-118** (Mapped Section Handling - CORRECT):
```python
if canonical_key:
    logical_section_data[canonical_key] = field.value or ""
    if field.preview_present and canonical_key not in previews:
        previews[canonical_key] = PreviewArtifact(
            field_key=canonical_key,
            artifact_type="unknown",
            files=[],
            notes=field.preview_hint,
        )
```

**Fix Required**: Apply same preview handling logic to unmapped sections:
- Check `field.preview_present` in unmapped sections
- Generate field key from section + field name
- Create PreviewArtifact entries even for unmapped fields

---

## Recommendations

1. **Fix Mapper** (High Priority)
   - Extend unmapped section loop to handle preview fields
   - Generate consistent field keys for unmapped preview artifacts
   - Test with both mapped and unmapped preview fields

2. **Extend Logical Sections Mapping** (Medium Priority)
   - Consider adding currently unmapped sections to `logical_sections_and_keys.json`
   - Sections like "Segment Specific", "Land Documents", "Approval From Competent Authorities" are consistent across projects
   - This would convert them from unmapped → mapped, triggering preview capture

3. **Add Integration Test** (Medium Priority)
   - Create test case for preview extraction with real HTML
   - Verify both mapped and unmapped preview fields are captured
   - Test end-to-end from raw HTML → preview artifacts

---

## Next Steps

1. Update `mapper.py` to preserve preview information for unmapped sections
2. Test fix with current production data
3. Re-run crawl to verify preview files are downloaded
4. Validate preview artifacts in output directory


