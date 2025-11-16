"""CLI to load V1 JSON run outputs into the database."""
from __future__ import annotations

import argparse
from pathlib import Path

from cg_rera_extractor.db.loader import load_all_runs, load_run_into_db


def main() -> None:
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

    args = parser.parse_args()
    base_dir = Path(args.runs_dir).expanduser()

    if args.run_id:
        run_path = base_dir / args.run_id
        stats = load_run_into_db(str(run_path))
        print(f"Loaded run {args.run_id}: {stats}")
    else:
        stats = load_all_runs(str(base_dir))
        print(f"Loaded runs under {base_dir}: {stats}")


if __name__ == "__main__":
    main()
