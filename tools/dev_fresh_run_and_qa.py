"""One-shot developer smoke test combining a crawl and QA checks."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
import threading
from pathlib import Path
from typing import Iterable

import yaml


DEFAULT_CONFIG = Path("config.debug.yaml")
RUN_DIR_PREFIX = "run_"


@dataclass(frozen=True)
class RunArtifactSummary:
    run_dir: Path
    html_files: list[Path]
    json_files: list[Path]
    previews_dir: Path
    preview_projects: int
    preview_files: int


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fresh crawl + QA smoke test to ensure detail files are real."
    )
    parser.add_argument(
        "--mode",
        choices=["full", "listings-only"],
        default="full",
        help="Pass-through crawl mode for cg_rera_extractor.cli (default: %(default)s).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to crawl config file (default: {DEFAULT_CONFIG}).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    if not config_path.exists():
        sys.exit(f"Config file not found: {config_path}")

    output_base_dir = _resolve_output_base_dir(config_path)
    run_root = output_base_dir / "runs"
    run_root.mkdir(parents=True, exist_ok=True)

    crawl_cmd = [
        sys.executable,
        "-m",
        "cg_rera_extractor.cli",
        "--config",
        str(config_path),
        "--mode",
        args.mode,
    ]
    print(f"=== STEP 1: Running fresh crawl (mode={args.mode}) ===")
    _run_subprocess(crawl_cmd, fail_message="Crawl failed. See logs above.")

    print("=== STEP 2: Inspecting latest run artifacts ===")
    run_dir = _detect_latest_run(run_root)
    run_id = run_dir.name.removeprefix(RUN_DIR_PREFIX)
    print(f"Latest run detected: {run_dir}")

    artifacts = _summarize_artifacts(run_dir)
    qa_summary, qa_report = _run_field_by_field_qa_if_available(run_id, run_dir)

    _print_final_summary(args.mode, artifacts, qa_summary, qa_report)


def _resolve_output_base_dir(config_path: Path) -> Path:
    config_data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    try:
        output_base = config_data["run"]["output_base_dir"]
    except KeyError as exc:
        raise SystemExit(
            f"run.output_base_dir missing in config: {config_path}"
        ) from exc

    output_base_path = Path(output_base)
    if not output_base_path.is_absolute():
        output_base_path = (config_path.parent / output_base_path).resolve()
    return output_base_path


def _run_subprocess(cmd: list[str], fail_message: str) -> CommandResult:
    process = subprocess.Popen(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    threads: list[threading.Thread] = []
    if process.stdout:
        threads.append(
            threading.Thread(
                target=_forward_stream,
                args=(process.stdout, sys.stdout, stdout_lines),
                daemon=True,
            )
        )
    if process.stderr:
        threads.append(
            threading.Thread(
                target=_forward_stream,
                args=(process.stderr, sys.stderr, stderr_lines),
                daemon=True,
            )
        )
    for thread in threads:
        thread.start()

    returncode = process.wait()

    for thread in threads:
        thread.join()

    stdout_text = "".join(stdout_lines)
    stderr_text = "".join(stderr_lines)
    if returncode != 0:
        print(fail_message, file=sys.stderr)
        sys.exit(returncode)

    return CommandResult(returncode=returncode, stdout=stdout_text, stderr=stderr_text)


def _detect_latest_run(run_root: Path) -> Path:
    candidates = [p for p in run_root.iterdir() if p.is_dir() and p.name.startswith(RUN_DIR_PREFIX)]
    if not candidates:
        raise SystemExit(f"No run directories found under {run_root}.")
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    return latest


def _summarize_artifacts(run_dir: Path) -> RunArtifactSummary:
    raw_html_dir = run_dir / "raw_html"
    scraped_json_dir = run_dir / "scraped_json"
    previews_dir = run_dir / "previews"

    html_files = sorted(raw_html_dir.glob("*.html"))
    json_files = sorted(scraped_json_dir.glob("*.json"))

    if not raw_html_dir.exists() or not html_files:
        raise SystemExit(
            f"No detail HTML files found in {raw_html_dir}. Run may have failed to fetch details."
        )
    if not scraped_json_dir.exists() or not json_files:
        raise SystemExit(
            f"No scraped JSON files found in {scraped_json_dir}. Run may have failed to map projects."
        )

    preview_projects = 0
    preview_files = 0
    if previews_dir.exists():
        project_dirs = [d for d in previews_dir.iterdir() if d.is_dir()]
        preview_projects = len(project_dirs)
        preview_files = sum(1 for path in previews_dir.rglob("*") if path.is_file())

    print(f"Sample detail HTML: {html_files[0]}")
    print(f"Sample V1 JSON:     {json_files[0]}")
    print("=== STEP 3: Checking preview artifacts ===")
    if preview_projects and preview_files:
        sample_preview = _first_file(previews_dir.rglob("*"))
        preview_example = sample_preview if sample_preview else "(no file sample found)"
        print(
            f"Preview artifacts: {preview_projects} projects with {preview_files} files total "
            f"(e.g. {preview_example})"
        )
    else:
        print("No previews folder found for this run (or previews folder is empty).")

    return RunArtifactSummary(
        run_dir=run_dir,
        html_files=html_files,
        json_files=json_files,
        previews_dir=previews_dir,
        preview_projects=preview_projects,
        preview_files=preview_files,
    )


def _run_field_by_field_qa_if_available(
    run_id: str, run_dir: Path
) -> tuple[dict | None, Path | None]:
    qa_script = Path("tools/run_field_by_field_qa.py")
    if not qa_script.exists():
        print("Field-by-field QA script not found. Skipping QA step.")
        return None, None

    print("=== STEP 4: Running field-by-field QA ===")
    _run_subprocess(
        [
            sys.executable,
            str(qa_script),
            "--run-id",
            run_id,
        ],
        fail_message="Field-by-field QA failed.",
    )

    qa_report = run_dir / "qa_fields" / "qa_fields_report.json"
    if not qa_report.exists():
        print(f"QA report not generated at {qa_report}.")
        return None, qa_report

    try:
        summary = json.loads(qa_report.read_text(encoding="utf-8")).get("summary")
    except json.JSONDecodeError as exc:
        print(f"Could not parse QA JSON at {qa_report}: {exc}", file=sys.stderr)
        summary = None
    if summary:
        print(f"QA summary: {summary}")
    return summary, qa_report


def _print_final_summary(
    crawl_mode: str,
    artifacts: RunArtifactSummary,
    qa_summary: dict | None,
    qa_report: Path | None,
) -> None:
    print("\n=== DEV FRESH RUN & QA SUMMARY ===")
    print(f"Crawl mode: {crawl_mode}")
    print(f"Run dir: {artifacts.run_dir}")
    print(f"Detail HTML files: {len(artifacts.html_files)}")
    print(f"V1 JSON files:     {len(artifacts.json_files)}")
    if artifacts.preview_projects:
        print(
            f"Preview artifacts: {artifacts.preview_projects} projects, "
            f"{artifacts.preview_files} files."
        )
    else:
        print("Preview artifacts: none detected.")

    if qa_summary:
        print("Field-by-field QA:")
        for key in (
            "total_projects",
            "total_fields",
            "match",
            "mismatch",
            "missing_in_html",
            "missing_in_json",
            "preview_unchecked",
        ):
            value = qa_summary.get(key, 0)
            print(f"  {key}: {value}")
        if qa_report:
            print(f"QA report: {qa_report}")
    else:
        print("Field-by-field QA: skipped or report unavailable.")

    print("Detail HTML folder:", artifacts.run_dir / "raw_html")
    print("V1 JSON folder:", artifacts.run_dir / "scraped_json")
    if artifacts.previews_dir.exists():
        print("Previews folder:", artifacts.previews_dir)


def _first_file(paths: Iterable[Path]) -> Path | None:
    for candidate in paths:
        if candidate.is_file():
            return candidate
    return None


def _forward_stream(pipe, sink, buffer: list[str]) -> None:
    try:
        for chunk in pipe:
            sink.write(chunk)
            sink.flush()
            buffer.append(chunk)
    finally:
        pipe.close()


if __name__ == "__main__":
    main()
