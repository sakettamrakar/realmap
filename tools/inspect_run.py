#!/usr/bin/env python3
"""Summarize outputs from a single CG RERA crawl run."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def _load_run_dir(path_or_id: str, base_dir: Path) -> Path:
    """Resolve a run directory from a path or run_id."""

    candidate = Path(path_or_id).expanduser()
    if candidate.exists():
        return candidate

    run_dir = base_dir / "runs" / path_or_id
    if run_dir.exists():
        return run_dir

    run_dir_prefixed = base_dir / "runs" / f"run_{path_or_id}"
    if run_dir_prefixed.exists():
        return run_dir_prefixed

    message = (
        f"Could not find run directory for '{path_or_id}'. "
        f"Tried {candidate}, {run_dir}, and {run_dir_prefixed}."
    )
    raise FileNotFoundError(message)


def _count_listings(listing_files: Iterable[Path]) -> tuple[int, int]:
    """Return number of listing files and total listing rows."""

    total_rows = 0
    file_count = 0
    for path in listing_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, list):
            total_rows += len(payload)
        file_count += 1
    return file_count, total_rows


def inspect_run(path_or_id: str, base_dir: str) -> None:
    """Print a concise summary of a run's key outputs."""

    run_dir = _load_run_dir(path_or_id, Path(base_dir))
    listings_dir = run_dir / "listings"
    scraped_json_dir = run_dir / "scraped_json"
    run_report = run_dir / "run_report.json"

    print(f"Run directory: {run_dir}")
    if not run_dir.exists():
        raise SystemExit("Run directory does not exist.")

    listing_files = sorted(listings_dir.glob("*.json")) if listings_dir.exists() else []
    listing_file_count, listing_row_count = _count_listings(listing_files)
    print(f"Listings: {listing_row_count} rows across {listing_file_count} file(s)")

    v1_files = sorted(scraped_json_dir.glob("*_v1.json")) if scraped_json_dir.exists() else []
    print(f"V1 project payloads: {len(v1_files)} file(s)")

    if run_report.exists():
        payload = json.loads(run_report.read_text(encoding="utf-8"))
        counts = payload.get("counts", {})
        print("Run report:")
        print(f"  Mode: {payload.get('mode')}")
        print(f"  Filters: {payload.get('filters_used')}")
        print(f"  Counts: {counts}")
        errors = payload.get("errors") or []
        warnings = payload.get("warnings") or []
        print(f"  Errors: {errors if errors else 'none'}")
        print(f"  Warnings: {warnings if warnings else 'none'}")
    else:
        print("run_report.json not found.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a CG RERA crawl run output folder.")
    parser.add_argument("path_or_id", help="Run directory path or run_<id> identifier")
    parser.add_argument(
        "--base-dir",
        default="./outputs",
        help="Base outputs directory to search when a run ID is provided (default: ./outputs)",
    )
    args = parser.parse_args()

    inspect_run(args.path_or_id, args.base_dir)


if __name__ == "__main__":  # pragma: no cover - manual helper
    main()
