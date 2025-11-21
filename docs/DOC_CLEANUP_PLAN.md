# Doc Cleanup Plan (temporary)

Inventory of existing docs and how they overlap:

- `README.md` – repo intro, outdated vs current crawler/QA/DB flows.
- `USER_GUIDE.md` – main user guide with crawl/QA/DB/API steps; supersedes README.
- `AI_Instructions.md` – AI agent rules; repeats architecture notes now covered elsewhere.
- `DEV_PLAN.md` – historical development plan; superseded by current code and should fold into a concise developer guide.
- `PROJECT_STATUS.md` – dated todo/status log; fold key context into developer guide or archive.
- `TEST_PLAYBOOK.md` – quick testing checklist; overlaps with QA docs/self-check notes.
- `REAL_CRAWL_GUIDE.md` – example real crawl flow; overlaps with user guide.
- `LOGGING_AND_STATE_MANAGEMENT_IMPROVEMENTS.md` – describes logging improvements; minor dev note.
- `BROWSER_CLOSURE_FIX.md`, `CAPTCHA_BROWSER_FIXES.md` – tactical fixes for browser issues; should be archived with a pointer.
- QA doc cluster: `QA_QUICK_START.md`, `QA_TESTING_GUIDE.md`, `QA_TESTING_INDEX.md`, `QA_TEST_SUITE_SUMMARY.md`, `QA_ARCHITECTURE_DIAGRAMS.md`, `QA_DELIVERY_SUMMARY.md`, `QA_FIX_PLAN.md`, `IMPLEMENTATION_SUMMARY.md` – overlapping QA quick start, test index, and summaries; consolidate into a single QA guide.
- Preview docs: `PREVIEW_EXTRACTION_TEST_REPORT.md`, `PREVIEW_FIX_VERIFICATION.md` – preview/QA validation notes; archive after pulling any actionable notes into QA guide.
- DB doc cluster: `DB_QUICK_REFERENCE.md`, `DB_PIPELINE_VERIFICATION.md`, `DB_DEBUG_SESSION_COMPLETION.md`, `DB_IMPLEMENTATION_SUMMARY.md`, `DB_DELIVERABLES.md`, `DB_DOCUMENTATION_INDEX.md`, `DB_LOADING_TEST_RESULTS.md` – redundant DB quick ref/test reports and summaries; consolidate into a single DB guide.
- Cleanup/session docs: `CLEANUP_QUICK_REFERENCE.md`, `CLEANUP_SUMMARY.md`, `CLEANUP_VERIFICATION.md`, `SESSION_SUMMARY_20251117.md` – phase summaries; archive.
- `QA_ARCHITECTURE_DIAGRAMS.md` (large diagrams) – duplicate context; archive after distilling essentials into QA guide.
- Run artifacts: `outputs/**/qa_fields_report.md` – generated reports; leave untouched.

Target minimal doc set:

- `README.md` – primary entry: what the project does (crawler + preview + QA + DB), prerequisites, quick start for crawl/QA/DB, and pointers to deeper docs.
- `docs/DEV_GUIDE.md` – architecture overview and developer workflows (system_full_check, dev_fresh_run_and_qa, extending selectors/mappings, testing).
- `docs/QA_GUIDE.md` – single source for QA tooling (field-by-field QA, preview notes), how to run and interpret reports.
- `docs/DB_GUIDE.md` – DB schema overview and commands (init_db, load_runs_to_db, check_db_counts) with troubleshooting.
- `AI_Instructions.md` – trimmed AI agent expectations pointing to the above guides.

Planned actions:

- Merge user-facing instructions from `USER_GUIDE.md` and `REAL_CRAWL_GUIDE.md` into `README.md` and archive the originals.
- Create the new guides under `docs/` and fold relevant content from DEV/QA/DB clusters.
- Archive redundant/stale docs under `docs/_archive/` with a top-of-file note pointing to the canonical guides.
- Update links in README/AI Instructions to the new structure.
