"""CLI to load V1 JSON run outputs into the database."""
from __future__ import annotations

import argparse
from pathlib import Path

from cg_rera_extractor.db.loader import load_all_runs, load_run_into_db


def find_latest_run_id(base_dir: Path) -> str | None:
    """Return the most recent run_* directory name under ``base_dir`` if present."""

    if not base_dir.exists():
        return None

    candidates = [path for path in base_dir.iterdir() if path.is_dir() and path.name.startswith("run_")]
    if not candidates:
        return None

    return sorted(candidate.name for candidate in candidates)[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Load V1 JSON runs into the database")
    parser.add_argument(
        "--runs-dir",
        default="./runs",
        help="Base directory containing run_* folders (default: ./runs)",
    )
    parser.add_argument(
        "--run-id",
        help="Specific run ID (e.g., run_20240101_120000) to load; loads all runs if omitted",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Load only the most recent run_* directory under --runs-dir",
    )

    args = parser.parse_args()
    if args.run_id and args.latest:
        parser.error("--run-id and --latest are mutually exclusive")

    base_dir = Path(args.runs_dir).expanduser()

    if args.latest:
        latest = find_latest_run_id(base_dir)
        if latest is None:
            print(f"No run_* directories found under {base_dir}")
            return 1
        args.run_id = latest

    if args.run_id:
        run_path = base_dir / args.run_id
        if not run_path.exists():
            print(f"Run path {run_path} does not exist")
            return 1
        stats = load_run_into_db(str(run_path))
        print(f"Loaded run {args.run_id}: {stats}")
    else:
        stats = load_all_runs(str(base_dir))
        print(f"Loaded runs under {base_dir}: {stats}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
