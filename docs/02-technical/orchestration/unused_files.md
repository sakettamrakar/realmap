# 🧹 Unused Files Report

An analysis of the repository identified several standalone scripts and potential cleanup candidates. These files are not imported by the main application flow and typically serve adjacent utility purposes.

## 🔴 Standalone Scripts (Root Level)

These files are located in the root directory and should likely be moved to `tools/` or `tests/` to keep the root clean.

| File | Size | Proposed Action |
|------|------|-----------------|
| `download_pdfs.py` | 12.8KB | Move to `tools/` or merge into `cli`. |
| `integrate_pdf_extractions.py` | 23.7KB | Critical workflow script; move to `tools/`. |
| `regenerate_v1_json.py` | 6.8KB | Move to `tools/` |
| `analyze_json.py` | 1.1KB | Move to `tools/debug/` |
| `check_ai_health.py` | 1.2KB | Merge with `check_health.py` or move to `tools/`. |
| `debug_*.py` | Various | Move all `debug_*.py` scripts to `tools/debug/`. |
| `find_good_pdf.py` | 1.2KB | Move to `tools/debug/`. |
| `inspect_db.py` | 1.2KB | Duplicate of `tools/data_audit_query.py`? Check & Delete. |
| `run_loader.py` | 0.8KB | Duplicate of `tools/load_runs_to_db.py`. Delete. |
| `verify_db.py` | 0.9KB | Redundant. Delete. |

## 🟡 Test Files (Root Level)

These files pollute the root namespace and should be moved to `tests/`.

*   `test_e2e_scoring.py`
*   `test_full_llm_extraction.py`
*   `test_gpu_llm.py`
*   `test_llm_detailed.py`
*   `test_llm_extraction.py`
*   `test_llm_fixed.py`
*   `test_llm_integration.py`
*   `test_llm_quick.py`

## 📊 Redundancy Analysis

Potential duplicates found during scanning:

1.  **DB Loader Scripts**: `run_loader.py` vs `tools/load_runs_to_db.py`. The latter is more robust.
2.  **Health Checks**: `check_health.py`, `check_ai_health.py`, and `tools/system_full_check.py`. Consolidate into the system check tool.
3.  **Analysis Tools**: `inspect_db.py` vs `tools/data_audit_query.py`.

## ✅ Recommended Cleanup Plan

1.  Create `tools/debug/` and move all `debug_*.py` and `inspect_*.py` files there.
2.  Move all `test_*.py` files from root to `tests/`.
3.  Move `analyze_json.py`, `download_pdfs.py`, `integrate_pdf_extractions.py`, `regenerate_v1_json.py` to `tools/`.
4.  Delete `run_loader.py` and `verify_db.py` after confirming functionality exists in `tools/`.
