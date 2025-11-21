# AI Coding Instructions

This repository is a CG RERA (Chhattisgarh) extraction + QA + DB toolkit. These notes keep AI assistants aligned with the project's expectations.

## Scope and boundaries

- Extract listings and detail pages from the CG RERA portal, map to normalized V1 scraper JSON, and support QA + DB loading. Manual CAPTCHA solving is required; do not bypass protections.
- Keep concerns separated: browser/session helpers, listing navigation, detail fetching, parsing/mapping, QA utilities, and DB loaders.
- Config-driven: selectors, run modes, caps, and paths come from YAML configs (`config.example.yaml`, `config.phase2.sample.yaml`) and `DATABASE_URL` for DB tools.

## Coding conventions

- Python 3.10+, Playwright for browser control, BeautifulSoup for parsing, pytest for tests.
- Prefer small modules with clear responsibilities; keep HTML parsing logic testable against fixtures.
- Preserve run output structure: `listings/`, `raw_html/`, `raw_extracted/`, `scraped_json/`, `qa_fields/`, plus `run_report.json`.

## Workflows to prefer

- Health checks before changes: `python tools/self_check.py` or `python tools/system_full_check.py`.
- Dev smoke: `python tools/dev_fresh_run_and_qa.py` to validate crawl + QA in one shot.
- DB verification: `python tools/check_db_counts.py` after `load_runs_to_db.py`.

## What not to do

- Do not automate CAPTCHA solving or attempt site evasion tactics.
- Do not hard-code search filters, paths, or credentials into code; keep them in configs/env vars.
- Do not mix parsing/mapping logic with network or browser code.

## Where to read more

- User entrypoint and quick commands: `README.md`
- Architecture and workflows: `docs/DEV_GUIDE.md`
- QA tooling: `docs/QA_GUIDE.md`
- Database loading: `docs/DB_GUIDE.md`
