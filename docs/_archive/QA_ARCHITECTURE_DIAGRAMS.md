ARCHIVED - superseded by docs/QA_GUIDE.md.

# QA Testing Architecture & Data Flow

## Complete QA Smoke Testing Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   QA SMOKE TEST ORCHESTRATOR                             │
│            (dev_fresh_run_and_qa.py)                                     │
└──────────────────────────┬──────────────────────────────────────────────┘
                          │
           ┌──────────────┴──────────────┐
           │                            │
      STEP 1                       STEP 2
    CRAWL                      INSPECT ARTIFACTS
           │                            │
           ▼                            ▼
    ┌─────────────┐            ┌──────────────┐
    │   Browser   │            │  Check for   │
    │  Crawler    │            │  - HTML      │
    │             │            │  - JSON      │
    │ Download    │            │  - Previews  │
    │ Details     │            │              │
    └──────┬──────┘            └──────┬───────┘
           │                          │
           ▼                          │
    ┌─────────────────────────────┐   │
    │   outputs/runs/run_X/        │   │
    │   ├── raw_html/              │   │
    │   │   ├── project_1.html     │   │
    │   │   ├── project_2.html     │   │
    │   │   └── ...                │   │
    │   ├── scraped_json/          │   │
    │   │   ├── project_1.v1.json  │   │
    │   │   ├── project_2.v1.json  │   │
    │   │   └── ...                │   │
    │   └── previews/              │   │
    │       └── [screenshots]      │   │
    └─────────────────────────────┘   │
                                       │
                                  Success?
                                  Yes│
                                      │
                                      └──┐
                                         │
                                    STEP 3
                                  QA CHECK
                                         │
                                         ▼
    ┌───────────────────────────────────────────────────────────┐
    │          FIELD-BY-FIELD COMPARISON                        │
    │              (run_field_by_field_qa.py)                   │
    └───────────┬─────────────────────────────────────┬─────────┘
                │                                     │
       ┌────────┴──────────┐              ┌──────────┴────────┐
       │                   │              │                   │
    For each              │              │            ┌──────▼────┐
    project:          Diff[]         Report()        │  QA Output │
       │                   │              │          │  Files     │
       ▼                   │              │          │            │
    ┌─────────┐            │              │          └────────────┘
    │ Load    │            │              │
    │ HTML    │            │              │
    └────┬────┘            │              │
         │                 │              │
         ▼                 │              │
    ┌──────────────┐       │              │
    │field_        │       │              │
    │extractor.py │       │              │
    │             │       │              │
    │Extract      │       │              │
    │Label-Value  ├──┐    │              │
    │Map          │  │    │              │
    └──────────────┘  │    │              │
                      │    │              │
                      ▼    │              │
                  html_    │              │
                  fields = │              │
                  {         │              │
                   "reg":   │              │
                   "001",   │              │
                   ...      │              │
                  }         │              │
                            │              │
                      ┌─────┴─────┐        │
                      │           │        │
                      ▼           ▼        │
                  ┌──────────────────┐    │
                  │ Load V1 Project  │    │
                  │ JSON             │    │
                  │                  │    │
                  │ v1_project = {   │    │
                  │  registration:   │    │
                  │  "001",          │    │
                  │  ...             │    │
                  │ }                │    │
                  └────────┬─────────┘    │
                           │              │
                      ┌────┴──────┐       │
                      │           │       │
                      ▼           ▼       │
                   ┌─────────────────────────┐
                   │ compare_v1_to_html_     │
                   │ fields.py               │
                   │                         │
                   │ For each mapped field:  │
                   │ 1. Extract JSON value   │
                   │ 2. Get HTML value       │
                   │ 3. Normalize both       │
                   │ 4. Compare              │
                   │ 5. Classify status      │
                   └────────┬────────────────┘
                            │
                            ▼
                        FieldDiff[]
                        {
                          "field_key": "...",
                          "json_value": "...",
                          "html_value": "...",
                          "status": "match|
                                     mismatch|
                                     missing_in_html|
                                     missing_in_json|
                                     preview_unchecked"
                        }
                            │
                            │
                    ┌───────┴────────┐
                    │                │
              Per-Project         Overall
              Results            Summary
                    │                │
                    ▼                ▼
            ┌────────────────────────────┐
            │   QA Report Generation      │
            │   - JSON report             │
            │   - Markdown report         │
            │   - Statistics              │
            └────────────────────────────┘
                        │
                        ▼
         ┌──────────────────────────┐
         │  outputs/runs/run_X/      │
         │  qa_fields/               │
         │  ├── qa_fields_report.json│
         │  └── qa_fields_report.md  │
         └──────────────────────────┘
```

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          TEST SUITE                                      │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  UNIT TESTS (tests/qa/)                                          │  │
│  │  ┌────────────────────┐  ┌──────────────────────────────────┐   │  │
│  │  │ test_field_        │  │ test_field_by_field_             │   │  │
│  │  │ extractor.py       │  │ compare.py                       │   │  │
│  │  │                    │  │                                  │   │  │
│  │  │ Tests:             │  │ Tests:                           │   │  │
│  │  │ • HTML parsing     │  │ • Comparison logic               │   │  │
│  │  │ • Label extraction │  │ • Match detection                │   │  │
│  │  │ • Value extraction │  │ • Mismatch detection             │   │  │
│  │  │ • Preview handling │  │ • Missing field detection        │   │  │
│  │  │ • Normalization    │  │ • Status classification          │   │  │
│  │  └────────────────────┘  └──────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  INTEGRATION TESTS (tests/test_qa_smoke.py)                      │  │
│  │                                                                   │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │  │
│  │  │ HTML         │  │ V1 JSON      │  │ Field Comparison     │   │  │
│  │  │ Extraction   │  │ Parsing      │  │ Logic                │   │  │
│  │  │              │  │              │  │                      │   │  │
│  │  │ • Extract    │  │ • Parse      │  │ • Match detection    │   │  │
│  │  │ • Normalize  │  │ • Validate   │  │ • Mismatch detection │   │  │
│  │  │ • Handle     │  │ • Null       │  │ • Missing detection  │   │  │
│  │  │   Preview    │  │   values     │  │ • Preview handling   │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘   │  │
│  │                                                                   │  │
│  │  ┌─────────────────────────┐  ┌──────────────────────────────┐   │  │
│  │  │ Smoke Test Integration  │  │ Edge Cases                   │   │  │
│  │  │                         │  │                              │   │  │
│  │  │ • Complete workflow     │  │ • Whitespace normalization   │   │  │
│  │  │ • Report generation     │  │ • Case-insensitive compare   │   │  │
│  │  │ • Resilience with       │  │ • None/empty handling        │   │  │
│  │  │   missing data          │  │                              │   │  │
│  │  │ • Resilience with       │  │                              │   │  │
│  │  │   extra data            │  │                              │   │  │
│  │  └─────────────────────────┘  └──────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  CLI HELPER TOOL (tools/test_qa_helper.py)                       │  │
│  │                                                                   │  │
│  │  Commands:                                                        │  │
│  │  • unit     - Run unit tests                                     │  │
│  │  • smoke    - Run integration tests                              │  │
│  │  • crawl    - Run fresh crawl + QA                               │  │
│  │  • qa       - Run QA on existing run                             │  │
│  │  • list     - List available runs                                │  │
│  │  • inspect  - View run results                                   │  │
│  │  • compare  - Compare single project                             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow: HTML to JSON Comparison

```
INPUT: HTML File (project_CG-REG-001.html)
│
├─ <table>
│  ├─ <tr><td>Registration Number</td><td>CG-REG-001</td></tr>
│  ├─ <tr><td>Project Name</td><td>Garden Villas</td></tr>
│  ├─ <tr><td>District</td><td>Raipur</td></tr>
│  └─ ...
│
▼
[field_extractor.py] - Extract Label-Value Pairs
│
├─ Normalize label: "Registration Number" → "registration_number"
├─ Extract value text: "CG-REG-001"
├─ Handle Preview buttons: "Preview" → special marker
└─ Collapse whitespace
│
▼
HTML Fields Dictionary
│
├─ "registration_number": "CG-REG-001"
├─ "project_name": "Garden Villas"
├─ "district": "Raipur"
└─ ...
│
├─────────────────────────────────────────┤
│                                          │
INPUT: V1 JSON (project_CG-REG-001.v1.json)
│
├─ {
│    "project_details": {
│      "registration_number": "CG-REG-001",
│      "project_name": "Garden Villas",
│      "district": "Raipur",
│      ...
│    }
│  }
│
▼
[field_by_field_compare.py] - Compare Fields
│
For each mapped field:
├─ Extract JSON value from path (e.g., "project_details.registration_number")
├─ Get HTML value from dict
├─ Normalize both:
│  ├─ Collapse whitespace: "  Value  " → "Value"
│  └─ Lowercase: "VALUE" → "value"
├─ Compare normalized values
└─ Classify status:
   ├─ Match: normalized values equal
   ├─ Mismatch: values differ
   ├─ Missing in JSON: JSON value is None
   ├─ Missing in HTML: HTML value is empty/missing
   └─ Preview unchecked: value is "Preview"
│
▼
FieldDiff List
│
├─ {
│    "field_key": "project_details.registration_number",
│    "json_value": "CG-REG-001",
│    "html_value": "CG-REG-001",
│    "status": "match"
│  },
│  {
│    "field_key": "project_details.tehsil",
│    "json_value": "Abhanpur",
│    "html_value": "Tilda",
│    "status": "mismatch"
│  },
│  ...
│
▼
[Report Generation]
│
├─ Aggregate results across all projects
├─ Calculate statistics:
│  ├─ total_fields
│  ├─ match_count
│  ├─ mismatch_count
│  ├─ missing_in_html_count
│  ├─ missing_in_json_count
│  └─ preview_unchecked_count
├─ Generate JSON report
└─ Generate Markdown summary
│
▼
OUTPUT: QA Reports
├─ qa_fields_report.json (detailed)
└─ qa_fields_report.md (summary)
```

## Test Execution Flow

```
TEST EXECUTION
│
├─ STEP 1: Load Fixtures
│  └─ tests/qa/fixtures/
│     ├─ detail_page.html
│     └─ project_v1.json
│
├─ STEP 2: Run Unit Tests
│  ├─ test_field_extractor.py
│  │  └─ Extract fields from HTML ✓
│  └─ test_field_by_field_compare.py
│     └─ Compare V1 vs HTML ✓
│
├─ STEP 3: Run Integration Tests
│  ├─ TestHTMLFieldExtraction (6 tests)
│  ├─ TestV1ProjectParsing (4 tests)
│  ├─ TestFieldComparison (8 tests)
│  ├─ TestQASmokeTestIntegration (4 tests)
│  └─ TestQAEdgeCases (3 tests)
│
├─ STEP 4: Generate Reports
│  └─ Aggregate all test results
│
└─ STEP 5: Display Summary
   ├─ Total tests: 28
   ├─ Passed: 28 ✓
   ├─ Failed: 0
   ├─ Execution time: ~0.6s
   └─ Coverage: All QA components
```

## Run Directory Structure

```
outputs/runs/run_20251117_123456/
│
├── raw_html/
│   ├── project_CG-REG-001.html      (Downloaded from RERA)
│   ├── project_CG-REG-002.html
│   ├── project_CG-REG-003.html
│   └── ... (50+ HTML files)
│
├── scraped_json/
│   ├── project_CG-REG-001.v1.json   (Extracted data)
│   ├── project_CG-REG-002.v1.json
│   ├── project_CG-REG-003.v1.json
│   └── ... (50+ JSON files)
│
├── previews/
│   ├── CG-REG-001/
│   │   ├── preview_0.png
│   │   └── preview_1.png
│   ├── CG-REG-002/
│   │   └── ...
│   └── ... (Screenshots of preview pages)
│
├── qa_fields/
│   ├── qa_fields_report.json        (Full QA results)
│   │   {
│   │     "summary": {
│   │       "run_id": "20251117_123456",
│   │       "total_projects": 50,
│   │       "total_fields": 450,
│   │       "match": 420,
│   │       "mismatch": 15,
│   │       "missing_in_html": 10,
│   │       "missing_in_json": 5,
│   │       "preview_unchecked": 0
│   │     },
│   │     "projects": [...]
│   │   }
│   │
│   └── qa_fields_report.md          (Summary table)
│       # Field-by-field QA Report
│       | Project | Mismatches | ... |
│       | --------|-----------|-----|
│       | CG-REG-001 | 2 | ... |
│       | ... |
│
└── [other artifacts]
   ├── crawl_log.txt
   ├── config.yaml
   └── ...
```

## Test Status Levels

```
┌──────────────────────────────────────────────────┐
│  RED ZONE (FAILING)                              │
│  • Unit tests fail                               │
│  • HTML extraction broken                        │
│  • JSON parsing broken                           │
│  → Cannot proceed to integration testing         │
│  → Fix code and re-run unit tests                │
└──────────────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│  YELLOW ZONE (PARTIAL)                           │
│  • Unit tests pass                               │
│  • Integration tests have failures               │
│  • Some edge cases not handled                   │
│  • Some comparison logic issues                  │
│  → Can proceed with caution                      │
│  → Fix identified issues                         │
└──────────────────────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────┐
│  GREEN ZONE (HEALTHY)                            │
│  • All unit tests pass                           │
│  • All integration tests pass                    │
│  • All edge cases handled                        │
│  • Reports generated correctly                   │
│  ✓ Ready for production use                      │
│  ✓ Run full smoke test                           │
│  ✓ Compare real-world data                       │
└──────────────────────────────────────────────────┘
```

---

**Visual Reference Created:** November 17, 2025
**Architecture Version:** 1.0

