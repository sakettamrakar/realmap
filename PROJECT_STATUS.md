# Project Status

## Overview
- The repository follows the architecture described in `DEV_PLAN.md`: config, browser, listing, detail, parsing, and run orchestration layers are all in place with accompanying fixtures and unit tests.
- Run orchestrator now supports DRY_RUN / LISTINGS_ONLY / FULL modes plus per-run caps for search combinations and total listings to keep live runs safe.
- Core parsing, mapping, and orchestration flows can be exercised offline via the new `tools/self_check.py` script and the existing pytest suite (17 tests).
- Jira integration tooling (`tools/jira_client.py`, `tools/sync_dev_plan_to_jira.py`, `.github/workflows/jira-sync.yml`) is wired up and ready to sync plan tasks to Jira once credentials are provided.

## Implementation Status vs DEV_PLAN
| DEV_PLAN task | Status | Notes |
| --- | --- | --- |
| P1.1 – Repo bootstrap | ✅ | Repository initialized with docs (`README.md`, `AI_Instructions.md`, `DEV_PLAN.md`) and pyproject config. |
| P1.2 – Package layout | ✅ | Module tree matches plan; tests ensure imports work. |
| P2.1 – Config models | ✅ | `cg_rera_extractor.config.models` implements all models; defaults hardened (e.g., browser timeout). |
| P2.2 – Config loader | ✅ | `load_config` reads YAML and validates via Pydantic; sample config + tests exist. |
| P2-T2 – Run modes and safety limits | ✅ | DRY_RUN / LISTINGS_ONLY / FULL modes plus search/listing caps implemented with tests and CLI override. |
| P3.1 – BrowserSession abstraction | ⚠️ | Playwright session implemented but only protocol-level tests exist; no live Playwright smoke test yet. |
| P3.2 – Manual CAPTCHA helper | ⚠️ | Blocking `input()` helper exists; no ergonomics for CLI prompt customisation. |
| P3.3 – Browser tests | ⚠️ | Fake session tests cover protocol but not real browser lifecycle. |
| P4.1 – Listing models | ✅ | `ListingRecord` dataclass mirrors schema. |
| P4.2 – Listing parser | ✅ | Robust header matching + fixture tests. |
| P4.3 – Listing tests | ✅ | Fixture-driven tests in `tests/test_listing_scraper.py`. |
| P5.1 – Storage helpers | ✅ | `make_project_html_path` / `save_project_html` implemented + tested. |
| P5.2 – Detail fetcher | ✅ | `fetch_and_save_details` implemented; tests cover fake session writes. |
| P5.3 – Detail tests | ✅ | Covered by `tests/test_detail_fetcher.py` & `tests/test_detail_storage.py`. |
| P6.1 – Raw models | ✅ | `FieldRecord`, `SectionRecord`, `RawExtractedProject` created. |
| P6.2 – Raw extractor | ✅ | HTML parsing covers table/inline layouts. |
| P6.3 – Raw extractor tests | ✅ | `tests/test_raw_extractor.py` uses fixture HTML. |
| P7.1 – V1 schema models | ✅ | `cg_rera_extractor.parsing.schema` defines V1 dataclasses. |
| P7.2 – Logical section mapping | ⚠️ | Static mapping JSON loaded at import; needs documentation and expansion for edge cases. |
| P7.3 – Mapper | ⚠️ | Works for basic flows; limited fixture coverage (single happy-path sample). |
| P7.4 – Mapper tests | ⚠️ | Only one sample verified; no negative-case coverage. |
| P8.1 – Run metadata | ✅ | `RunStatus` dataclass implemented; serialized to `run_report.json` for each run. |
| P8.2 – Orchestrator | ⚠️ | Full pipeline implemented; relies on Playwright + manual CAPTCHA so real runs remain brittle. |
| P8.3 – CLI | ⚠️ | `cg_rera_extractor.cli` exists but lacks automated tests and documentation/examples beyond config file. |
| P8.4 – Orchestrator tests | ⚠️ | `test_orchestrator_skeleton.py` covers a happy path with fakes only. |
| P9.1 – CONTRIBUTING / PR template | ❌ | No contributing guide or PR template yet. |
| P9.2 – Branch/PR guidance | ❌ | No automation around branch naming or templates. |

## Data Quality & Normalization
- Normalization layer trims whitespace, title-cases districts, standardizes project status/type labels, and cleans registration numbers before V1 JSON is written.
- Validation currently flags missing district/status, malformed pincodes found in mapped project details, and non-positive area figures (land or total area) for basic data-quality checks.
- Validation messages are stored alongside each V1 project payload and aggregated into `dq_warnings` counters during a run.

## Task T1–T7 Alignment
| Task | Scope | Status | Notes |
| --- | --- | --- | --- |
| T1 – Configuration layer | ✅ | Models + loader implemented, sample config + tests present. |
| T2 – Parsing primitives | ✅ | Raw extractor, schema models, fixtures, and tests complete. |
| T3 – Mapping to V1 | ⚠️ | Mapper functional with one sample; needs more fixtures for edge coverage. |
| T4 – Browser abstraction | ⚠️ | Protocol defined but no integration smoke test for Playwright. |
| T5 – Listing scraping | ✅ | Parser resilient to header variants; fixture tests verify behaviour. |
| T6 – Detail fetch/storage | ✅ | Storage helpers and fetcher validated with fake session tests. |
| T7 – Orchestrator & CLI | ⚠️ | Pipeline implemented and unit-tested with fakes; manual CAPTCHA + browser dependency makes real runs fragile. |

## Jira Integration Status
- `tools/jira_client.py` reads credentials from `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, and optional `JIRA_PROJECT_KEY` (default `CGRE`). No credentials are committed.
- `tools/sync_dev_plan_to_jira.py` parses `DEV_PLAN.md`, maintains `tools/jira_mapping.json`, and uses the Jira client to create/update issues; tests validate parsing and dry-run logic via monkeypatching.
- `.github/workflows/jira-sync.yml` (unchanged) invokes the sync script; ensure secrets are configured in GitHub Actions before enabling.
- There is **no built-in `JIRA_DRY_RUN` flag**; to avoid Jira writes run the sync script only when the required env vars are unset (it will error) or mock the client as in tests.
- Comment for Jira: "Run modes (DRY_RUN, LISTINGS_ONLY, FULL) and global safety limits implemented and tested for orchestrator."

## Testing Status
- ✅ `pytest` (24 tests) exercises config loader, storage, listing parser, raw extractor, mapper, data-quality layer, Jira sync parser, and orchestrator wiring with fakes (including run-mode/limit coverage).
- ✅ `python tools/self_check.py` runs an offline smoke-test suite (imports, config load, listing parse, raw extraction, mapper, orchestrator dry-run using fixtures).
- ✅ `python tools/parser_regression.py record` / `check` records and validates golden JSON outputs for HTML fixtures to catch upstream CG RERA UI changes.
- Manual CLI / Playwright runs are still required for real CG RERA scraping because CAPTCHA and browser interactions cannot be automated in CI.

## Known Gaps / TODOs
- No CONTRIBUTING.md / PR template (DEV_PLAN Phase 9 outstanding).
- Mapper & logical-section coverage limited to a single happy-path fixture; expand fixtures to cover more sections and failure cases.
- Browser layer lacks integration smoke tests; verifying Playwright launch/headless behaviour currently requires manual testing.
- CLI ergonomics (help text, examples, dry-run support) could be improved; currently only barebones instructions exist.
- Jira sync lacks a native dry-run mode; consider adding `JIRA_DRY_RUN=1` support to avoid accidental writes during local experiments.

## Run Output & Reports
- Each run now writes outputs under `<output_base_dir>/runs/run_<run_id>/` with standardized subfolders:

  ```
  runs/
    run_<run_id>/
      listings/
        listings_<district>_<status>.json
      raw_html/
        project_<reg_no>.html
      raw_extracted/
        project_<reg_no>.json
      scraped_json/
        project_<reg_no>.v1.json
      run_report.json
  ```

- `run_report.json` serializes the `RunStatus` for the run (mode, filters used, counts for search combinations/listings/details/projects mapped, warnings, and errors) to aid debugging and machine-readable tracking.

## Manual Test Checklist
### Quick offline checks (no network/browser needed)
1. `pytest`
   - Expect all 24 tests to pass (see per-test progress and summary `24 passed`).
2. `python tools/self_check.py`
   - Should print six PASS lines (imports, config, listing, raw extractor, mapper, orchestrator) and a summary `6/6 checks passed`.
3. `python -c "from cg_rera_extractor.config.loader import load_config; print(load_config('config.example.yaml').model_dump())"`
   - Confirms config loading and prints the parsed AppConfig dictionary.
4. Parser regression harness
   - Record/update a golden for a new HTML file: `python tools/parser_regression.py record path/to/file.html --fixtures-dir tests/parser_regression/fixtures --golden-dir tests/parser_regression/golden`
   - Compare parser output to existing goldens: `python tools/parser_regression.py check --fixtures-dir tests/parser_regression/fixtures --golden-dir tests/parser_regression/golden`
   - Run the `check` command before and after parser changes to confirm whether CG RERA HTML or parsing logic has shifted.

### Optional integration checks
1. CLI orchestrator dry-run against local config (requires Playwright + manual CAPTCHA):
   - `python -m cg_rera_extractor.cli --config config.example.yaml`
   - Expect browser launch, manual CAPTCHA prompt, log output per district/status, and run status summary with counts.
2. Jira sync (only with valid credentials):
   - `JIRA_BASE_URL=... JIRA_EMAIL=... JIRA_API_TOKEN=... python tools/sync_dev_plan_to_jira.py`
   - Expect console lines such as `Created CGRE-XX for task ...` followed by a summary; run only when you intend to sync.
3. Manual detail storage spot-check:
   - After running the orchestrator, inspect `outputs/<run>/raw_html` to ensure HTML files exist, and `raw_extracted` / `scraped_json` contain JSON payloads.

## Phase 2 Manual Run Playbook (P2-T4)
Follow this scripted manual flow to execute a very small live crawl end-to-end.

1. Environment prep
   - Ensure Python environment is active and dependencies installed (`pip install -e .[dev]` if needed).
   - (Optional) Run `pytest` to confirm the local environment is healthy.
2. Dry-run sanity check
   - Command: `python -m cg_rera_extractor.cli --config config.phase2.sample.yaml --mode dry-run`
   - Expect printed pairs such as `district=Raipur, status=Ongoing` and a note about the global listing cap.
3. Configure for the first pass
   - Open `config.phase2.sample.yaml` and ensure `run.mode` is set to `LISTINGS_ONLY`.
   - Keep the provided limits (`max_search_combinations: 2`, `max_total_listings: 50`) and output path (`./outputs/phase2_runs`).
4. Execute the constrained listings run
   - Command: `python -m cg_rera_extractor.cli --config config.phase2.sample.yaml`
   - In the launched browser: solve CAPTCHA when prompted, then click **Search** when ready.
   - Expect console logs like `Parsed X listings for Raipur / Ongoing` and a capped count per search (max 50).
5. Verify outputs
   - A new folder should appear under `outputs/phase2_runs/runs/` named `run_<id>`.
   - Inside the run directory:
     - `listings/` should contain small JSON and HTML snapshots for each district/status.
     - `run_report.json` should list the mode, filters, counts, and no errors; warnings should be empty unless listings were truncated.
6. Optional tiny FULL run
   - Edit `config.phase2.sample.yaml` to set `run.mode: FULL` while keeping the same safety limits.
   - Re-run `python -m cg_rera_extractor.cli --config config.phase2.sample.yaml`.
   - Expect additional outputs in `raw_html/`, `raw_extracted/`, and `scraped_json/` plus `projects_mapped`/`dq_warnings` counts in `run_report.json`.
7. Light inspection
   - Use `python tools/inspect_run.py run_<id> --base-dir ./outputs/phase2_runs` to summarize listing counts, V1 JSON count, and any reported errors.
8. Jira note
   - After a successful live run, add a Jira comment for P2-T4: “Executed a small live crawl end-to-end using the Phase 2 playbook; outputs captured under outputs/phase2_runs.”

Expected observations
- Log lines per search combination: `Running search for district=<name> status=<status>` followed by `Parsed X listings for <district> / <status>`.
- `run_report.json` should show low counts that align with the caps (search_combinations_attempted ≤ 2, listings_parsed ≤ 50) and `errors: []`.
