"""Export a high-level leaderboard of projects to CSV."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from cg_rera_extractor.analysis.projects import export_projects_csv


DEFAULT_EXPORT_DIR = Path("exports")


def _default_path(district: str | None, limit: int) -> Path:
    slug = (district or "all").replace(" ", "_").lower()
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return DEFAULT_EXPORT_DIR / f"top_projects_{slug}_limit{limit}_{timestamp}.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--district", help="Filter by district name", default=None)
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Number of projects to export (default: 50)",
    )
    parser.add_argument(
        "--min-score", type=int, default=None, help="Only include projects with this overall_score or higher"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path. Defaults to exports/top_projects_*.csv",
    )
    args = parser.parse_args()

    output_path = args.output or _default_path(args.district, args.limit)

    export_projects_csv(
        filters={
            "district": args.district,
            "limit": args.limit,
            "min_score": args.min_score,
        },
        path=output_path,
    )

    print(f"Exported to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
