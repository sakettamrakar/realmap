# Scraper Engine

This document describes the CG RERA scraper engine, run modes, and configuration.

## Components

- `browser/`: Playwright session management, context options, CAPTCHA handling.
- `listing/`: Search combinations, pagination, and listing parsing.
- `detail/`: Detail page fetch and optional preview capture.
- `parsing/`: Field extraction and V1 JSON mapping.
- `outputs/`: Run directory layout and artifact naming.

See `DEV_GUIDE.md` for a deeper developer-focused overview.

## Run Modes

The orchestrator supports multiple run modes (see `runs/orchestrator.py`):

- `dry-run`: Validate config and search filters without browser.
- `listings-only`: Collect listing pages and JSON without detail HTML.
- `full`: End-to-end scrape: listings + detail pages + V1 mapping.

Typical command (example):

```bash
python -m cg_rera_extractor.cli run --config config.debug.yaml --mode full
```

## Configuration

Configs are YAML files (see `config.example.yaml`, `config.debug.yaml`):

- `run.mode`: `dry-run`, `listings-only`, or `full`.
- `run.output_base_dir`: Base directory for `runs/run_<id>/`.
- `browser.headless`: `true`/`false` for Playwright.
- `search_page.selectors.*`: CSS/XPath selectors for search form and results.
- `db.url`: Database connection string for loader/QA tools.

## Run Directory Layout

Each run directory contains:

- `raw_html/`: Detail page HTML snapshots.
- `scraped_json/`: Normalized V1 JSON per project.
- `logs/`: Run logs for debugging.
- `qa_fields/`: QA reports (when QA tools are run).

## Error Handling & Observability

- The crawler logs step-by-step progress and errors to console and log files.
- Manual CAPTCHA handling: when a CAPTCHA is detected, the CLI waits for user input and prints instructions.
- Selector drift: if listing/detail selectors change, runs log missing elements and fail fast.

See `Debug-Runbook.md` for concrete troubleshooting steps.
