# Phase 6 – Analyst Tools

These utilities let internal power users query the CG RERA database without
needing to write SQL. They reuse the same database connection setup as the API
(`DATABASE_URL` must be configured) and emit lightweight text or CSV outputs.

## Quickstart

- Show a single project summary:
  ```bash
  python tools/show_project_summary.py --reg CG-RERA-PRJ-12345
  # or by database ID
  python tools/show_project_summary.py --project-id 42
  ```

- Export the top projects by score:
  ```bash
  python tools/export_top_projects.py --district Raipur --limit 20 --min-score 60
  ```

Outputs are written to the current working directory. CSV exports default to the
`exports/` folder.

## Workflows

### Inspect a project in depth
1. Identify the project registration number (from a crawl or API response).
2. Run `python tools/show_project_summary.py --reg <REG_NUMBER>`.
3. Review the printed sections:
   - **Project:** basic metadata and RERA status.
   - **Scores:** amenity/location/overall scores + version.
   - **Onsite amenities:** project-provided facilities.
   - **Location context:** nearby amenities and proximity highlights.

### Find the top 20 projects in Raipur by `overall_score`
1. Ensure `DATABASE_URL` is configured (same as used for the API/DB tools).
2. Run:
   ```bash
   python tools/export_top_projects.py --district Raipur --limit 20
   ```
3. Open the generated `exports/top_projects_raipur_limit20_<timestamp>.csv`
   in your spreadsheet or notebook.

### Ad-hoc exploration in notebooks
1. Import the analysis helpers:
   ```python
   from cg_rera_extractor.analysis.projects import get_project_summary, top_projects_by_score
   ```
2. Pull quick slices without touching SQL:
   ```python
   df = pandas.DataFrame(top_projects_by_score(district="Bilaspur", limit=100))
   df.overall_score.describe()
   ```

## Notes
- All helpers share the API's DB session factory; confirm connectivity with
  `python tools/check_db_counts.py` if you hit connection issues.
- `min_score` is inclusive. Use it to avoid noisy low-scoring projects when
  exporting CSVs.
- The analysis layer is read-only and does not mutate data.
