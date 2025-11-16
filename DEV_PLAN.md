# CG RERA Data Collection Framework – Development Plan

> This document describes a **step-by-step implementation plan** for the CG RERA Extraction Framework.  
> It is written so that an AI coding assistant (OpenAI Codecs, Copilot, etc.) can split it into **concrete tasks** and implement them in small, testable steps.

This plan assumes the high-level context from:

- `AI_Instructions.md`
- The existing CG RERA schema pack (V1 scraper JSON, logical sections, SQL schemas).

---

## 0. Conventions

- Language: **Python 3.10+**
- Test framework: **pytest**
- Browser automation: **Playwright**
- HTML parsing: **BeautifulSoup4**
- Config models: **pydantic/dataclasses**

Git & PR workflow:

- Create feature branches per task.
- Every PR must include tests.
- Every PR must pass `pytest`.

---

## 1. Phase 1 – Repository Setup & Layout

### P1.1: Initialize repo & Python project

- Create root folder.
- Add `.gitignore`.
- Add `README.md`, `AI_Instructions.md`, `DEV_PLAN.md`.
- Add `pyproject.toml` or `requirements.txt`.

### P1.2: Base package layout

```
cg_rera_extractor/
  config/
  browser/
  listing/
  detail/
  parsing/
  runs/
  outputs/
tests/
```

Add minimal imports and sanity tests.

---

## 2. Phase 2 – Configuration & Models

### P2.1: Config models

Create:

- `RunMode` (DRY_RUN, LISTINGS_ONLY, FULL)
- `SearchFilterConfig`
- `RunConfig`
- `BrowserConfig`
- `AppConfig`

### P2.2: Config loader

Create `load_config(path)`.

Add sample `config.example.yaml`.

Add unit tests.

---

### P2-T2 – Run modes and safety limits

- Add runtime guardrails (DRY_RUN/LISTINGS_ONLY/FULL) to orchestrator and CLI.
- Apply per-run caps for search combinations and listings processed.
- Ensure run status captures counts for planned/processed combinations and capped listings.

---

### P2-T1 – Wire orchestrator to real CG RERA search page

- Connect the orchestrator Playwright flow to the live CG RERA project search page.
- Centralize search URLs and selectors for district/status/project type fields.
- Implement manual CAPTCHA pause, listing HTML capture, and max-results guard for safe, low-volume runs.

---

### P2-T3 – Logging, run reports & output structure

- Standardize run outputs under `<output_base_dir>/runs/run_<run_id>/` with dedicated subfolders for listings, raw HTML, raw extracted JSON, and mapped scraper JSON.
- Emit a machine-readable `run_report.json` per run containing run metadata, filters used, counts, warnings, and errors.
- Improve console/log output for start/end of runs, per-filter combinations, listing counts, truncation notices, and summarized exceptions.

---

## 3. Phase 3 – Browser Session & Manual CAPTCHA

### P3.1: BrowserSession abstraction

Methods:

- start()
- goto()
- fill()
- click()
- wait_for_selector()
- close()

### P3.2: Manual CAPTCHA helper

```
input("Solve CAPTCHA, then press ENTER...")
```

### P3.3: Tests

Mock BrowserSession for tests.

---

### P3-T1 – DB schema & connection layer (Postgres)

- Add `DatabaseConfig` wired to `DATABASE_URL`/`config.db.url`.
- Introduce SQLAlchemy engine helper + `SessionLocal` factory.
- Create normalized models for projects, promoters, buildings, unit types, documents, and quarterly updates with a natural key on `state_code + rera_registration_number`.
- Provide a lightweight schema initializer (e.g., `tools/init_db.py`) for local setups.

---

## 4. Phase 4 – Listing Page Scraper

### P4.1: Listing models

`ListingRecord` fields:
- reg_no
- project_name
- promoter_name
- district
- tehsil
- status
- detail_url
- run_id

### P4.2: Listing HTML parser

`parse_listing_html(html)` using BeautifulSoup.

### P4.3: Tests

Fixture: listing_sample.html.

---

## 5. Phase 5 – Detail Page Fetcher & HTML Storage

### P5.1: Storage helpers

Functions:
- make_project_html_path()
- save_project_html()

### P5.2: Fetcher

Fetch detail pages using BrowserSession; save HTML.

### P5.3: Tests

Use fake browser session.

---

## 6. Phase 6 – HTML → Raw Extracted JSON

### P6.1: Raw-extracted structures

Models:
- FieldRecord
- SectionRecord
- RawExtractedProject

### P6.2: Raw extractor implementation

`extract_raw_from_html(html)`.

Logic:
- Detect sections (h1–h6, strong)
- Extract label/value
- Detect links
- Classify TEXT/NUMBER/DATE/URL

### P6.3: Tests

Use provided sample HTML fixtures.

---

## 7. Phase 7 – Mapping to V1 Scraper JSON

### P7.1: V1 schema models

Create full V1 schema models based on `v1_scraper_json_schema_example.json`.

### P7.2: Logical section mapping

`logical_sections_and_keys.json` → in-memory map.

### P7.3: Mapper

`map_raw_to_v1(raw)`.

Fill:
- metadata
- project_details
- promoter_details
- land_details
- building_details
- unit_types
- bank_details
- documents
- quarterly_updates

### P7.4: Tests

Check mapping correctness.

---

## 8. Phase 8 – Run Orchestrator & CLI

### P8.1: Run metadata

`RunStatus` with run_id, started_at, finished_at, counts, errors.

### P8.2: Orchestrator

Steps:

1. Generate run_id
2. Create output dirs
3. Start browser
4. For each filter set:
   - Go to search page
   - Fill fields
   - Manual CAPTCHA wait
   - Scrape listings
   - Fetch detail pages
5. Close browser
6. Parse raw + map to V1

### P8.3: CLI

`cli.py` with Typer or argparse.

### P8.4: Tests

Mock browser + fixture HTML → run mini workflow.

---

## 9. Phase 9 – SDLC & PR Workflow

### P9.1: CONTRIBUTING.md

- PEP8/Black
- Every PR must have tests
- No untested features
- No giant files; modules only

### P9.2: Branch/PR naming

- `feature/<task>`

Add PR template.

---

## 10. How AI Assistants Should Use This Plan

- Treat each task as a small PR.
- Respect the layered architecture.
- Never bypass CAPTCHA.
- Maintain data flow:
  **Listing → Detail HTML → RawExtracted → V1 JSON**.

---

This plan is the actionable roadmap for development.
