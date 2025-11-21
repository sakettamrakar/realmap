# QA Guide

Field-by-field QA compares detail page HTML against normalized V1 JSON produced by the crawler.

## Inputs and outputs

- Inputs: a completed run directory with `raw_html/` (detail pages) and `scraped_json/` (V1 JSON).
- Outputs: `qa_fields/qa_fields_report.json` and `.md` under the run directory. The helper prints a summary to the console.

## Tools

- Fresh crawl + QA smoke (recommended default):  
  `python tools/dev_fresh_run_and_qa.py --mode full --config config.debug.yaml`
- QA on an existing run:  
  `python tools/run_field_by_field_qa.py --run-id <run_id> [--limit 10 | --project-key CG-REG-001]`
- Helper menu (list runs, inspect summaries, run QA/compare specific projects):  
  `python tools/test_qa_helper.py list|inspect|qa|compare`

## Reading the report

Each project entry enumerates field-level statuses:

- `match` – HTML and JSON values align after normalization.
- `mismatch` – Values differ; review HTML and parser/mapping.
- `missing_in_html` – Present in JSON but not detected in HTML (check selectors or page content).
- `missing_in_json` – Present in HTML but absent from JSON (likely parser gap).
- `preview_unchecked` – Value came from a preview interaction; requires manual confirmation if previews are not captured.

Normalization before comparison collapses whitespace, trims edges, and compares case-insensitively.

## Typical workflows

- Quick validation on a small run: `python tools/run_field_by_field_qa.py --run-id <id> --limit 5`
- Investigate a single project: `python tools/run_field_by_field_qa.py --run-id <id> --project-key CG-REG-001`
- Generate crawl + QA artifacts in one go for debugging: `python tools/dev_fresh_run_and_qa.py --mode listings-only` (fast) or `--mode full` (end-to-end).

## Troubleshooting

- No HTML files found: confirm the crawl completed detail fetches and the config `run.output_base_dir` matches the run path.
- Sudden mismatch spikes: inspect recent parser changes and compare HTML snapshots in `raw_html/`. Run with `--project-key` to isolate.
- Lots of `preview_unchecked`: ensure preview capture is enabled where applicable and that the detail fetcher waited for dynamic content.
- QA scripts read from disk only; if performance is slow, use `--limit` or filter to a project key.
