# CG RERA Data Collection Framework – AI Coding Instructions

> This repository contains a **data collection (Extraction) framework** for **Chhattisgarh RERA (Real Estate Regulatory Authority)** real-estate projects.

The goal is to help AI coding assistants (OpenAI Codecs / Copilot etc.) understand:

- What this project is about
- What we are **allowed** to do
- What the high-level architecture is
- How to structure code, configs, and tests

---

## 1. Project Goal & Scope

### 1.1 Goal

Build a **reliable, testable, and extensible data collection framework** that:

- Scrapes **Chhattisgarh RERA project data** from the official CG RERA portal.
- Handles **manual CAPTCHA solving** (we do NOT bypass CAPTCHAs).
- Produces structured outputs in:
  - Raw HTML (per project)
  - Raw extracted JSON (sections + fields)
  - Normalized V1 scraper JSON (canonical schema)

This is the **E in ETL** (Extraction) only. Transformation and loading to DB may be separate modules / repos.

### 1.2 Scope (V1)

- **State**: Chhattisgarh (CG) only.
- **Source site**: CG RERA official project search + project detail views.
- **Entities we care about**:
  - Projects
  - Promoters
  - Buildings / Towers / Blocks
  - Unit types (1BHK/2BHK/etc.)
  - Bank / Escrow accounts
  - Documents (PDFs / certificates)
  - Quarterly updates / progress

**Non-goals for V1**:

- No multi-state scraping (no Maharashtra etc. yet).
- No automatic CAPTCHA solving or security bypassing.
- No browser automation hacks to evade protections.
- No real-time streaming; batch runs are fine.

---

## 2. Key Constraints & Rules (IMPORTANT)

1. **Respect legal / ethical boundaries**
   - Do not attempt to break or bypass CAPTCHAs.
   - Assume a **human will manually solve CAPTCHA**; we only integrate the browser session.

2. **Separation of concerns**
   - Keep these layers logically separated:
     - Browser automation / session management
     - Listing scraping
     - Detail page fetching
     - HTML → raw JSON conversion
     - Raw JSON → normalized JSON mapping
     - Output writing / logging

3. **Config-driven**
   - No hard-coded values for:
     - Districts
     - Status filters
     - Paths
   - Use config files (`config.yaml`, `.env`, or similar) wherever possible.

4. **Testability**
   - Core parsing logic (HTML → JSON mapping) must be testable without hitting the live website.
   - Use **saved HTML** fixtures for unit tests.

5. **Idempotent & resumable runs (as far as possible)**
   - Running the same config twice should not corrupt data.
   - Re-runs over the same period/district should be safe.

---

## 3. High-Level Architecture (Modules)

Suggested structure:

cg_rera_extractor/
  config/
  browser/
  listing/
  detail/
  parsing/
  runs/
  outputs/
tests/

---

## 4. Data Flow Overview

1. Run orchestrator
2. Browser session + manual CAPTCHA
3. Listing scraper
4. Detail page fetcher
5. Raw extraction
6. Normalization
7. Output writing

---

## 5. Technologies (Preferred Defaults)

- Python 3.10+
- Playwright or Selenium
- BeautifulSoup4
- Pydantic or dataclasses
- pytest for tests

---

## 6. Manual CAPTCHA Handling

Use a simple pause:

input("Solve CAPTCHA in browser, then press ENTER to continue...")

---

## 7. Naming & Style Conventions

- snake_case for Python
- CapWords for classes
- No giant files; small modular code
- Docstrings everywhere

---

## 8. Summary for AI Assistants

- Think “CG RERA extraction pipeline”
- Do not bypass CAPTCHA
- Respect mappings and V1 scraper schema
- Follow the multi-layer architecture
