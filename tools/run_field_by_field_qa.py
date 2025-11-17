from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, TypedDict

from cg_rera_extractor.parsing.schema import V1Project
from cg_rera_extractor.qa.field_by_field_compare import compare_v1_to_html_fields
from cg_rera_extractor.qa.field_extractor import extract_label_value_map


class RunQASummary(TypedDict):
    run_id: str
    total_projects: int
    total_fields: int
    match: int
    mismatch: int
    missing_in_html: int
    missing_in_json: int
    preview_unchecked: int


class ProjectQADetail(TypedDict):
    project_key: str
    diffs: List[dict]


def _load_v1_project(path: Path) -> V1Project:
    data = path.read_text(encoding="utf-8")
    return V1Project.model_validate_json(data)


def _summarize_diffs(diffs: List[dict]) -> Dict[str, int]:
    summary = {
        "total_fields": len(diffs),
        "match": 0,
        "mismatch": 0,
        "missing_in_html": 0,
        "missing_in_json": 0,
        "preview_unchecked": 0,
    }
    for diff in diffs:
        status = diff.get("status")
        if status in summary:
            summary[status] += 1
    return summary


def run_field_by_field_qa(run_id: str, limit: int | None = None, project_key: str | None = None) -> dict:
    # Try multiple possible run locations
    possible_paths = [
        Path("runs") / f"run_{run_id}",  # Current directory
        Path("outputs/phase2_runs/runs") / f"run_{run_id}",  # Phase2 runs
        Path("outputs/debug_runs/runs") / f"run_{run_id}",  # Debug runs
    ]
    
    run_dir = None
    for path in possible_paths:
        if path.exists():
            run_dir = path
            break
    
    if run_dir is None:
        raise FileNotFoundError(f"Run directory not found for: {run_id}. Checked: {possible_paths}")

    html_dir = run_dir / "raw_html"
    json_dir = run_dir / "scraped_json"

    if not html_dir.exists() or not json_dir.exists():
        missing = []
        if not html_dir.exists():
            missing.append(str(html_dir))
        if not json_dir.exists():
            missing.append(str(json_dir))
        raise FileNotFoundError(f"Missing expected folders: {', '.join(missing)}")

    qa_output_dir = run_dir / "qa_fields"
    qa_output_dir.mkdir(parents=True, exist_ok=True)

    project_json_files = sorted(json_dir.glob("*.v1.json"))
    results: List[ProjectQADetail] = []

    if project_key:
        project_json_files = [p for p in project_json_files if project_key in p.stem]

    if limit is not None:
        project_json_files = project_json_files[:limit]

    overall_counts = RunQASummary(
        run_id=run_id,
        total_projects=0,
        total_fields=0,
        match=0,
        mismatch=0,
        missing_in_html=0,
        missing_in_json=0,
        preview_unchecked=0,
    )

    for json_path in project_json_files:
        key = json_path.stem.replace("project_", "", 1).replace(".v1", "")
        html_path = html_dir / f"project_{key}.html"
        if not html_path.exists():
            continue

        html_content = html_path.read_text(encoding="utf-8")
        html_fields = extract_label_value_map(html_content)
        v1_project = _load_v1_project(json_path)
        diffs = compare_v1_to_html_fields(v1_project, html_fields)

        summary_counts = _summarize_diffs(diffs)
        overall_counts["total_projects"] += 1
        overall_counts["total_fields"] += summary_counts["total_fields"]
        overall_counts["match"] += summary_counts["match"]
        overall_counts["mismatch"] += summary_counts["mismatch"]
        overall_counts["missing_in_html"] += summary_counts["missing_in_html"]
        overall_counts["missing_in_json"] += summary_counts["missing_in_json"]
        overall_counts["preview_unchecked"] += summary_counts["preview_unchecked"]

        results.append(ProjectQADetail(project_key=key, diffs=diffs))

    report = {"summary": overall_counts, "projects": results}

    qa_json_path = qa_output_dir / "qa_fields_report.json"
    qa_json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    md_lines = ["# Field-by-field QA Report", "", f"Run: {run_id}", ""]
    md_lines.append("| Project | Mismatches | Missing in HTML | Missing in JSON | Preview |")
    md_lines.append("| --- | --- | --- | --- | --- |")
    for project in results:
        counts = _summarize_diffs(project["diffs"])
        md_lines.append(
            "| "
            + project["project_key"]
            + " | "
            + str(counts["mismatch"])
            + " | "
            + str(counts["missing_in_html"])
            + " | "
            + str(counts["missing_in_json"])
            + " | "
            + str(counts["preview_unchecked"])
            + " |"
        )
    qa_md_path = qa_output_dir / "qa_fields_report.md"
    qa_md_path.write_text("\n".join(md_lines), encoding="utf-8")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run field-by-field QA between HTML and V1 JSON")
    parser.add_argument("--run-id", required=True, help="Run identifier, e.g. 20241121_010203")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit on number of projects to process")
    parser.add_argument("--project-key", default=None, help="Optional project key filter")
    args = parser.parse_args()

    report = run_field_by_field_qa(args.run_id, limit=args.limit, project_key=args.project_key)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
