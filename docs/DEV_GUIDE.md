# Developer Guide

This guide covers architecture, key scripts, and day-to-day workflows for the CG RERA extractor + QA + DB stack.

## Architecture (high level)

- `browser/`: Playwright session helpers and manual CAPTCHA pause.
- `listing/`: Search-page navigation, listing parsing, and search combination orchestration.
- `detail/`: Detail page fetchers plus optional preview capture helpers.
- `parsing/`: HTML-to-raw extraction and mapping to normalized V1 scraper JSON.
- `qa/`: Field extraction and comparison utilities used by the QA tools.
- `outputs/`: Run artifact naming/writing utilities.
- `db/`: Loader utilities used by the DB CLI tools.

### Run modes
- `dry-run`: Validate config and planned search combinations; no browser/network.
- `listings-only`: Collect listing pages/JSON without detail fetches.
- `full`: Listing scrape + detail HTML + raw extraction + V1 mapping.

## Core developer workflows

- Quick offline check: `python tools/self_check.py`
- Supervised system check (crawl + DB verification, logs to `logs/system_check_errors.log`):  
  `python tools/system_full_check.py`
- Dev smoke (fresh crawl + QA on the result):  
  `python tools/dev_fresh_run_and_qa.py --mode full --config config.debug.yaml`
- Inspect a run: `python tools/inspect_run.py --run-id <id>`
- Parser regression helper: `python tools/parser_regression.py` (compare parsed outputs on fixtures).

## Configs and conventions

- Start from `config.example.yaml` (FULL demo) or `config.phase2.sample.yaml` (safe LISTINGS_ONLY).  
- Key fields: `run.mode`, `run.output_base_dir`, `run.search_filters`, `browser.headless`, `db.url`, `search_page.selectors.*`.  
- Manual CAPTCHA: the CLI prints `Solve CAPTCHA...` and waits for ENTER. If selectors drift, the crawler may switch to manual filter mode and print instructions.

## Extending the crawler

- New search filters/selectors: update `config/search_page` entries and add guarded interactions in `listing/`.
- Detail parsing changes: adjust HTML parsing in `parsing/` and extend mapping to V1 JSON; add fixtures in `tests/` to cover cases.
- Preview handling: preview-specific notes live in the QA guide, but detail fetchers surface preview assets into the per-run `previews/` directory when enabled.
- Logging/state: the crawler emits step-by-step progress (search parameters, counts, detail fetch progress) to make long runs observable.

## QA and DB touchpoints

- QA jobs read `raw_html/` and `scraped_json/` from a run directory; see `docs/QA_GUIDE.md` for CLI details and status meanings.
- DB tools consume the same `scraped_json/` outputs; see `docs/DB_GUIDE.md` for schema basics and commands.

## Testing strategy

- Unit tests: `pytest tests/qa/` for field extraction/comparison, plus parsing and config tests across `tests/`.
- Smoke/integration: `pytest tests/test_qa_smoke.py` exercises the QA pipeline against fixtures.
- Full workflow check: `python tools/system_full_check.py` (runs crawl with sample config and DB verification).

## Troubleshooting notes

- Browser window will stay open until `BrowserSession.close()` runs; if a stray window hangs, close it manually and re-run.
- CAPTCHA or selector drift: switch `browser.headless` to `false`, run LISTINGS_ONLY with small caps, and update `search_page.selectors.*` in your config.
- If detail fetch counts are zero, confirm manual CAPTCHA was solved, check run logs, and verify the search page still matches configured selectors.
