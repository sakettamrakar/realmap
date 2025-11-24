# Data Inventory

## Overview
This document summarizes the existing data artifacts found in the repository, specifically within `outputs/realcrawl/runs`.

## Runs
- **Location**: `outputs/realcrawl/runs/`
- **Total Runs**: ~25 runs (e.g., `run_20251120_144252_994652` to `run_20251121_113347_558ae6`)
- **Representative Run**: `run_20251121_113347_558ae6`

## Artifacts per Run
Each run directory typically contains:

1.  **`scraped_json/`**:
    *   Contains V1 JSON files named `project_{state}_{reg_no}.v1.json`.
    *   Example: `project_CG_PCGRERA240218000002.v1.json`.
    *   Count: Varies per run (e.g., 2 projects in the representative run).

2.  **`previews/`**:
    *   Contains subdirectories named `{state}_{reg_no}` (e.g., `CG_PCGRERA240218000002`).
    *   These folders presumably contain downloaded preview assets (PDFs, images), although in the analyzed run, the JSON `previews` section referenced paths like `../Content/ProjectDocuments/...` which might be relative to the source HTML or a different base.
    *   *Note*: The JSON `previews` section has a `files` list which was empty in the sample, but `notes` contained file paths.

3.  **`raw_html/`**:
    *   Contains raw HTML files of the detail pages.
    *   Structure: `raw_html/{state}_{reg_no}/...` (inferred).

4.  **`raw_extracted/`**:
    *   Contains intermediate extraction outputs (likely JSON or text).

5.  **`run_report.json`**:
    *   Summary of the run execution.

## Data Linkage
- **Project Key**: `state_code` + `rera_registration_number` (e.g., `CG` + `PCGRERA240218000002`).
- **JSON File**: `scraped_json/project_{key}.v1.json`.
- **Preview Folder**: `previews/{key}/`.
- **DB Record**: `projects` table, keyed by `state_code` and `rera_registration_number`.

## Missing Artifacts
- **QA Reports**: No `qa_fields` or `qa_deep` directories were found in the searched runs.
