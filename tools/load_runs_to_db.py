"""CLI to load V1 JSON run outputs into the database."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Parse verbose flag early to configure logging before other imports
_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--verbose", action="store_true", help=argparse.SUPPRESS)
_args, _ = _parser.parse_known_args()

# Configure logging based on verbose flag
log_level = logging.DEBUG if _args.verbose else logging.INFO
logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
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
        default="./outputs/runs",
        help="Base directory containing run_* folders (default: ./outputs/runs)",
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
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show debug logging with details on skipped records",
    )

    args = parser.parse_args()
    if args.run_id and args.latest:
        parser.error("--run-id and --latest are mutually exclusive")

    base_dir = Path(args.runs_dir).expanduser()
    
    # Print database info
    db_url = ensure_database_url()
    print(f"\n{'='*70}")
    print(f"Database Loader")
    print(f"{'='*70}")
    print(f"Database target: {describe_database_target(db_url)}")
    print(f"Runs directory:  {base_dir.resolve()}")

    if args.latest:
        latest = find_latest_run_id(base_dir)
        if latest is None:
            print(f"\n✗ Error: No run_* directories found under {base_dir}")
            return 1
        args.run_id = latest

    try:
        if args.run_id:
            run_path = base_dir / args.run_id
            if not run_path.exists():
                print(f"\n✗ Error: Run path {run_path} does not exist")
                return 1
            print(f"\nLoading single run: {args.run_id}")
            stats = load_run_into_db(str(run_path))
        else:
            print(f"\nLoading all runs under {base_dir}")
            stats = load_all_runs(str(base_dir))

        # Print summary
        print(f"\n{'='*70}")
        print(f"Load Summary")
        print(f"{'='*70}")
        print(f"Projects upserted:    {stats.get('projects_upserted', 0):,}")
        print(f"Promoters inserted:   {stats.get('promoters', 0):,}")
        print(f"Buildings inserted:   {stats.get('buildings', 0):,}")
        print(f"Unit types inserted:  {stats.get('unit_types', 0):,}")
        print(f"Documents inserted:   {stats.get('documents', 0):,}")
        print(f"Quarterly updates:    {stats.get('quarterly_updates', 0):,}")
        
        runs_processed = stats.get('runs_processed', [])
        if runs_processed:
            print(f"\nRuns processed: {len(runs_processed)}")
            for run in runs_processed:
                print(f"  • {run}")
        
        print(f"\n✓ Load completed successfully!")
        print(f"{'='*70}\n")
        return 0

    except Exception as exc:
        print(f"\n✗ Error during load: {exc}")
        print(f"{'='*70}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
