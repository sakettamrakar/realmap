"""
Practical QA testing helper script.

This script provides an interactive interface for testing the QA smoke test
workflow. It can:
1. Run unit tests for QA components
2. Run the full smoke test
3. Inspect existing run results
4. Compare HTML vs JSON for specific projects
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from cg_rera_extractor.parsing.schema import V1Project
from cg_rera_extractor.qa.field_by_field_compare import compare_v1_to_html_fields
from cg_rera_extractor.qa.field_extractor import extract_label_value_map


def run_unit_tests(filter_pattern: Optional[str] = None) -> int:
    """Run QA unit tests."""
    cmd = [sys.executable, "-m", "pytest", "tests/qa/", "-v"]
    if filter_pattern:
        cmd.extend(["-k", filter_pattern])
    
    print("=" * 70)
    print("Running QA Unit Tests")
    print("=" * 70)
    result = subprocess.run(cmd)
    return result.returncode


def run_smoke_tests(filter_pattern: Optional[str] = None) -> int:
    """Run integration smoke tests."""
    cmd = [sys.executable, "-m", "pytest", "tests/test_qa_smoke.py", "-v"]
    if filter_pattern:
        cmd.extend(["-k", filter_pattern])
    
    print("=" * 70)
    print("Running QA Smoke Integration Tests")
    print("=" * 70)
    result = subprocess.run(cmd)
    return result.returncode


def run_fresh_crawl_and_qa(config_path: str = "config.debug.yaml", mode: str = "full") -> int:
    """Run full fresh crawl followed by QA."""
    cmd = [
        sys.executable,
        "-m",
        "tools.dev_fresh_run_and_qa",
        "--config",
        config_path,
        "--mode",
        mode,
    ]
    
    print("=" * 70)
    print(f"Running Fresh Crawl and QA (config={config_path}, mode={mode})")
    print("=" * 70)
    result = subprocess.run(cmd)
    return result.returncode


def run_qa_on_existing_run(
    run_id: str, limit: Optional[int] = None, project_key: Optional[str] = None
) -> int:
    """Run QA on an existing run."""
    cmd = [
        sys.executable,
        "tools/run_field_by_field_qa.py",
        "--run-id",
        run_id,
    ]
    if limit:
        cmd.extend(["--limit", str(limit)])
    if project_key:
        cmd.extend(["--project-key", project_key])
    
    print("=" * 70)
    print(f"Running QA on Run: {run_id}")
    if limit:
        print(f"  Limit: {limit} projects")
    if project_key:
        print(f"  Project Filter: {project_key}")
    print("=" * 70)
    result = subprocess.run(cmd)
    return result.returncode


def list_available_runs() -> list[str]:
    """List all available run directories."""
    runs_dir = Path("outputs/runs")
    if not runs_dir.exists():
        return []
    
    run_dirs = [d.name for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
    return sorted(run_dirs, reverse=True)  # Most recent first


def inspect_run_results(run_id: str) -> None:
    """Display QA results for a run."""
    # Find the run directory
    possible_paths = [
        Path("outputs/runs") / run_id,
        Path("outputs/phase2_runs/runs") / run_id,
        Path("outputs/debug_runs/runs") / run_id,
    ]
    
    run_dir = None
    for path in possible_paths:
        if path.exists():
            run_dir = path
            break
    
    if not run_dir:
        print(f"Run not found: {run_id}")
        return
    
    qa_report_path = run_dir / "qa_fields" / "qa_fields_report.json"
    qa_md_path = run_dir / "qa_fields" / "qa_fields_report.md"
    
    print("=" * 70)
    print(f"QA Results for Run: {run_id}")
    print("=" * 70)
    
    if qa_report_path.exists():
        report = json.loads(qa_report_path.read_text(encoding="utf-8"))
        summary = report.get("summary", {})
        
        print("\nSummary Statistics:")
        print(f"  Total Projects:        {summary.get('total_projects', 0)}")
        print(f"  Total Fields:          {summary.get('total_fields', 0)}")
        print(f"  Matches:               {summary.get('match', 0)}")
        print(f"  Mismatches:            {summary.get('mismatch', 0)}")
        print(f"  Missing in HTML:       {summary.get('missing_in_html', 0)}")
        print(f"  Missing in JSON:       {summary.get('missing_in_json', 0)}")
        print(f"  Preview Unchecked:     {summary.get('preview_unchecked', 0)}")
        
        total_fields = summary.get('total_fields', 0)
        if total_fields > 0:
            match_rate = (summary.get('match', 0) / total_fields) * 100
            print(f"\nMatch Rate: {match_rate:.1f}%")
        
        # Show project-level breakdown
        projects = report.get("projects", [])
        if projects:
            print(f"\nProject-Level Breakdown:")
            print(f"  {'Project':<20} {'Match':<10} {'Mismatch':<10} {'Missing HTML':<15} {'Missing JSON':<15}")
            print("  " + "-" * 70)
            
            for project in projects[:10]:  # Show first 10
                key = project.get("project_key", "Unknown")
                diffs = project.get("diffs", [])
                
                match_count = sum(1 for d in diffs if d.get("status") == "match")
                mismatch_count = sum(1 for d in diffs if d.get("status") == "mismatch")
                missing_html = sum(1 for d in diffs if d.get("status") == "missing_in_html")
                missing_json = sum(1 for d in diffs if d.get("status") == "missing_in_json")
                
                print(f"  {key:<20} {match_count:<10} {mismatch_count:<10} {missing_html:<15} {missing_json:<15}")
            
            if len(projects) > 10:
                print(f"\n  ... and {len(projects) - 10} more projects")
    
    if qa_md_path.exists():
        print(f"\nMarkdown Report: {qa_md_path}")
        print("Run: cat (Get-Content on Windows) to view the full report.")
    
    print(f"\nRun Directory: {run_dir}")
    print(f"  Raw HTML:   {run_dir / 'raw_html'}")
    print(f"  Scraped JSON: {run_dir / 'scraped_json'}")
    print(f"  QA Report:  {run_dir / 'qa_fields'}")


def compare_single_project(run_id: str, project_key: str) -> None:
    """Display field-by-field comparison for a single project."""
    # Find the run directory
    possible_paths = [
        Path("outputs/runs") / run_id,
        Path("outputs/phase2_runs/runs") / run_id,
        Path("outputs/debug_runs/runs") / run_id,
    ]
    
    run_dir = None
    for path in possible_paths:
        if path.exists():
            run_dir = path
            break
    
    if not run_dir:
        print(f"Run not found: {run_id}")
        return
    
    # Load HTML and JSON
    html_file = run_dir / "raw_html" / f"project_{project_key}.html"
    json_file = run_dir / "scraped_json" / f"project_{project_key}.v1.json"
    
    if not html_file.exists():
        print(f"HTML file not found: {html_file}")
        return
    
    if not json_file.exists():
        print(f"JSON file not found: {json_file}")
        return
    
    # Extract and compare
    html_content = html_file.read_text(encoding="utf-8")
    html_fields = extract_label_value_map(html_content)
    
    v1_project = V1Project.model_validate_json(json_file.read_text(encoding="utf-8"))
    diffs = compare_v1_to_html_fields(v1_project, html_fields)
    
    # Display results
    print("=" * 70)
    print(f"Field-by-Field Comparison: {project_key}")
    print("=" * 70)
    print()
    
    # Summary
    summary = {
        "match": sum(1 for d in diffs if d["status"] == "match"),
        "mismatch": sum(1 for d in diffs if d["status"] == "mismatch"),
        "missing_in_html": sum(1 for d in diffs if d["status"] == "missing_in_html"),
        "missing_in_json": sum(1 for d in diffs if d["status"] == "missing_in_json"),
        "preview_unchecked": sum(1 for d in diffs if d["status"] == "preview_unchecked"),
    }
    
    print(f"Summary: {summary['match']} match, {summary['mismatch']} mismatch, "
          f"{summary['missing_in_html']} missing in HTML, {summary['missing_in_json']} missing in JSON, "
          f"{summary['preview_unchecked']} preview unchecked")
    print()
    
    # Detailed comparison
    print(f"{'Field':<40} {'Status':<20} {'JSON Value':<25} {'HTML Value':<25}")
    print("-" * 110)
    
    for diff in diffs:
        field = diff["field_key"].replace("project_details.", "")
        status = diff["status"]
        json_val = str(diff["json_value"])[:25] if diff["json_value"] else "(null)"
        html_val = str(diff["html_value"])[:25] if diff["html_value"] else "(null)"
        
        print(f"{field:<40} {status:<20} {json_val:<25} {html_val:<25}")
    
    # Show issues
    issues = [d for d in diffs if d["status"] != "match"]
    if issues:
        print()
        print("=" * 70)
        print("Issues Details:")
        print("=" * 70)
        
        for diff in issues:
            if diff["status"] == "mismatch":
                print(f"\n❌ MISMATCH: {diff['field_key']}")
                print(f"   JSON:  {diff['json_value']}")
                print(f"   HTML:  {diff['html_value']}")
            elif diff["status"] == "missing_in_html":
                print(f"\n⚠️  MISSING IN HTML: {diff['field_key']}")
                print(f"   JSON:  {diff['json_value']}")
            elif diff["status"] == "missing_in_json":
                print(f"\n⚠️  MISSING IN JSON: {diff['field_key']}")
                print(f"   HTML:  {diff['html_value']}")
            elif diff["status"] == "preview_unchecked":
                print(f"\n❓ PREVIEW: {diff['field_key']}")
                print(f"   Requires user interaction (Preview button)")


def main() -> None:
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="QA Testing Helper - Interactive tool for testing the QA smoke test workflow."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Unit tests command
    unit_parser = subparsers.add_parser("unit", help="Run QA unit tests")
    unit_parser.add_argument(
        "-k", "--filter", help="Pytest filter pattern (e.g., 'test_extracts')"
    )
    
    # Smoke tests command
    smoke_parser = subparsers.add_parser("smoke", help="Run QA integration smoke tests")
    smoke_parser.add_argument(
        "-k", "--filter", help="Pytest filter pattern (e.g., 'test_complete')"
    )
    
    # Fresh crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Run fresh crawl + QA")
    crawl_parser.add_argument(
        "-c", "--config", default="config.debug.yaml", help="Config file path"
    )
    crawl_parser.add_argument(
        "-m", "--mode", default="full", choices=["full", "listings-only"],
        help="Crawl mode"
    )
    
    # Run QA on existing run
    qa_parser = subparsers.add_parser("qa", help="Run QA on existing run")
    qa_parser.add_argument("run_id", help="Run ID (e.g., run_20251117_123456)")
    qa_parser.add_argument(
        "-l", "--limit", type=int, help="Limit number of projects"
    )
    qa_parser.add_argument(
        "-p", "--project-key", help="Filter by project key"
    )
    
    # List runs command
    list_parser = subparsers.add_parser("list", help="List available runs")
    
    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect run results")
    inspect_parser.add_argument("run_id", help="Run ID to inspect")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare single project")
    compare_parser.add_argument("run_id", help="Run ID")
    compare_parser.add_argument("project_key", help="Project key (e.g., CG-REG-001)")
    
    args = parser.parse_args()
    
    if args.command == "unit":
        sys.exit(run_unit_tests(args.filter))
    elif args.command == "smoke":
        sys.exit(run_smoke_tests(args.filter))
    elif args.command == "crawl":
        sys.exit(run_fresh_crawl_and_qa(args.config, args.mode))
    elif args.command == "qa":
        sys.exit(run_qa_on_existing_run(args.run_id, args.limit, args.project_key))
    elif args.command == "list":
        runs = list_available_runs()
        if runs:
            print("\nAvailable Runs (most recent first):")
            for run in runs:
                run_path = Path("outputs/runs") / run
                if (run_path / "qa_fields" / "qa_fields_report.json").exists():
                    print(f"  ✓ {run} [has QA report]")
                else:
                    print(f"  • {run}")
        else:
            print("No runs found in outputs/runs/")
    elif args.command == "inspect":
        inspect_run_results(args.run_id)
    elif args.command == "compare":
        compare_single_project(args.run_id, args.project_key)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
