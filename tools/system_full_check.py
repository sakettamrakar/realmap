"""Run a supervised end-to-end system check for the CG RERA pipeline."""
from __future__ import annotations

import subprocess
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Sequence

from cg_rera_extractor.config.env import describe_database_target, ensure_database_url

CONFIG_PATH = "config.phase2.sample.yaml"
ERROR_LOG_PATH = Path("logs/system_check_errors.log")


@dataclass
class Step:
    name: str
    command: Sequence[str] | None = None
    runner: Callable[[Path], "StepResult"] | None = None
    skip: bool = False
    skip_reason: str | None = None


@dataclass
class StepResult:
    name: str
    command: Sequence[str] | None
    exit_code: int
    stdout: str
    stderr: str
    skipped: bool = False
    skip_reason: str | None = None


def log_error(step_name: str, command: Sequence[str] | None, exit_code: int, stderr: str, log_path: Path) -> None:
    """Append a structured error block for the failed step."""

    command_repr = " ".join(command) if command else "(custom step)"
    timestamp = datetime.now().isoformat()
    block = (
        f"[{timestamp}]\n"
        f"STEP: {step_name}\n"
        f"COMMAND: {command_repr}\n"
        f"EXIT CODE: {exit_code}\n"
        f"STDERR:\n{stderr or '(no stderr output)'}\n"
        "---\n"
    )
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(block)


def run_subprocess(command: Sequence[str]) -> StepResult:
    try:
        completed = subprocess.run(command, capture_output=True, text=True)
        return StepResult(
            name="",
            command=command,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    except FileNotFoundError as exc:  # Missing executable
        return StepResult(
            name="",
            command=command,
            exit_code=1,
            stdout="",
            stderr=str(exc),
        )


def api_import_check(_: Path) -> StepResult:
    """Try importing the FastAPI app module as a lightweight health check."""

    command = ["python", "-c", "import cg_rera_extractor.api.app"]
    try:
        import cg_rera_extractor.api.app  # noqa: F401
    except Exception:  # noqa: BLE001 - we want any import failure recorded
        return StepResult(
            name="API health check (import)",
            command=command,
            exit_code=1,
            stdout="",
            stderr=traceback.format_exc(),
        )

    return StepResult(
        name="API health check (import)",
        command=command,
        exit_code=0,
        stdout="",
        stderr="",
    )


def db_check_runner(_: Path) -> StepResult:
    """Check that data was actually loaded into the database."""
    
    command = ["python", "tools/check_db_counts.py"]
    try:
        import subprocess
        result = subprocess.run(command, capture_output=True, text=True)
        return StepResult(
            name="DB data verification",
            command=command,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    except Exception as exc:
        return StepResult(
            name="DB data verification",
            command=command,
            exit_code=1,
            stdout="",
            stderr=str(exc),
        )


def geo_qa_runner(_: Path) -> StepResult:
    """Run geo QA in non-blocking mode and surface the stdout."""

    command = [
        "python",
        "tools/check_geo_quality.py",
        "--sample-size",
        "3",
        "--output-json",
        "runs/system_geo_qa_report.json",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        stdout = result.stdout
        stderr = result.stderr
        if result.returncode != 0:
            stdout += (
                "\n(check_geo_quality exited with "
                f"{result.returncode}; treating as warning)\n"
            )
        return StepResult(
            name="Geo QA (non-blocking)",
            command=command,
            exit_code=0,
            stdout=stdout,
            stderr=stderr,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return StepResult(
            name="Geo QA (non-blocking)",
            command=command,
            exit_code=0,
            stdout="",
            stderr=str(exc),
        )


def amenity_score_qa_runner(_: Path) -> StepResult:
    """Run amenity/score QA without failing the overall check."""

    command = [
        "python",
        "tools/check_amenity_and_scores_quality.py",
        "--sample-size",
        "3",
        "--output-json",
        "runs/system_amenity_qa_report.json",
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        stdout = result.stdout
        stderr = result.stderr
        if result.returncode != 0:
            stdout += (
                "\n(check_amenity_and_scores_quality exited with "
                f"{result.returncode}; treating as warning)\n"
            )
        return StepResult(
            name="Amenity & score QA (non-blocking)",
            command=command,
            exit_code=0,
            stdout=stdout,
            stderr=stderr,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return StepResult(
            name="Amenity & score QA (non-blocking)",
            command=command,
            exit_code=0,
            stdout="",
            stderr=str(exc),
        )


def run_step(step: Step, index: int, total: int, log_path: Path) -> StepResult:
    banner = f"=== STEP {index}/{total}: {step.name} ==="
    print(banner)

    if step.skip:
        skip_message = f"Skipping {step.name}: {step.skip_reason or 'not applicable'}"
        print(skip_message)
        return StepResult(
            name=step.name,
            command=step.command,
            exit_code=0,
            stdout="",
            stderr="",
            skipped=True,
            skip_reason=step.skip_reason,
        )

    if step.runner:
        result = step.runner(log_path)
    elif step.command:
        result = run_subprocess(step.command)
    else:
        raise ValueError(f"Step {step.name} must define a command or runner")

    # Attach the name now that the StepResult has been produced
    result.name = step.name

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.exit_code != 0:
        log_error(step.name, result.command, result.exit_code, result.stderr, log_path)
        print(f"Step '{step.name}' failed (exit code {result.exit_code}).")
    else:
        print(f"Step '{step.name}' completed successfully.")

    print()
    return result


def build_steps(config_path: str) -> list[Step]:
    geocode_script = Path("tools/geocode_projects.py")
    geocode_step = Step(
        name="Geocoding batch (noop)",
        command=[
            "python",
            "tools/geocode_projects.py",
            "--config",
            config_path,
            "--limit",
            "10",
            "--mode",
            "noop",
        ],
    )
    if not geocode_script.exists():
        geocode_step.skip = True
        geocode_step.skip_reason = "geocode_projects.py not found"

    return [
        Step(name="Self-check", command=["python", "tools/self_check.py"]),
        Step(name="Pytest", command=["pytest"]),
        Step(
            name="DRY_RUN crawl",
            command=[
                "python",
                "-m",
                "cg_rera_extractor.cli",
                "--config",
                config_path,
                "--mode",
                "dry-run",
            ],
        ),
        Step(
            name="LISTINGS_ONLY crawl",
            command=[
                "python",
                "-m",
                "cg_rera_extractor.cli",
                "--config",
                config_path,
                "--mode",
                "listings-only",
            ],
        ),
        Step(
            name="FULL crawl",
            command=[
                "python",
                "-m",
                "cg_rera_extractor.cli",
                "--config",
                config_path,
                "--mode",
                "full",
            ],
        ),
        Step(name="DB schema init", command=["python", "tools/init_db.py"]),
        Step(
            name="Load latest run into DB",
            command=["python", "tools/load_runs_to_db.py", "--latest"],
        ),
        Step(
            name="DB data verification",
            runner=db_check_runner,
        ),
        geocode_step,
        Step(name="Geo QA (non-blocking)", runner=geo_qa_runner),
        Step(
            name="Amenity & score QA (non-blocking)",
            runner=amenity_score_qa_runner,
        ),
        Step(name="API health check", runner=api_import_check),
    ]


def summarize(results: Iterable[StepResult], log_path: Path) -> None:
    print("=== SYSTEM CHECK SUMMARY ===")
    any_failures = False
    for result in results:
        if result.skipped:
            status = "[SKIP]"
        elif result.exit_code == 0:
            status = "[OK]  "
        else:
            status = "[FAIL]"
            any_failures = True
        print(f"{status} {result.name}")

    if any_failures:
        print(f"\nOne or more steps failed. See {log_path} for details.")
    else:
        print("\nAll steps completed. No errors were logged.")
    print(f"Error log file: {log_path}")


def main() -> int:
    ERROR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Start fresh each time
    if ERROR_LOG_PATH.exists():
        ERROR_LOG_PATH.unlink()

    active_db_url = ensure_database_url()
    print(f"Using database target: {describe_database_target(active_db_url)}")

    steps = build_steps(CONFIG_PATH)
    results: list[StepResult] = []

    total = len(steps)
    for idx, step in enumerate(steps, start=1):
        result = run_step(step, idx, total, ERROR_LOG_PATH)
        results.append(result)

    summarize(results, ERROR_LOG_PATH)

    return 0 if all(r.exit_code == 0 for r in results if not r.skipped) else 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
