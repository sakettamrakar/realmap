"""Quick sanity checks for the Phase 6 read model.

This helper runs a few representative queries against the
`project_search_view` and prints basic stats so developers can
validate index effectiveness during tuning.
"""

from __future__ import annotations

import argparse
from textwrap import dedent

from sqlalchemy import text

from cg_rera_extractor.db import get_engine


def _print_header(title: str) -> None:
    print("\n" + title)
    print("=" * len(title))


def inspect_counts(conn) -> None:
    _print_header("Row counts")
    for table in ["projects", "project_scores", "project_amenity_stats", "project_locations", "project_search_view"]:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.scalar_one()
        print(f"{table:>24}: {count:,}")


def run_sample_queries(conn, district: str | None) -> None:
    params = {"district": district} if district else {}

    examples: list[tuple[str, str]] = [
        (
            "Top projects by overall_score",
            dedent(
                """
                SELECT project_id, project_name, district, tehsil, overall_score, registration_date
                FROM project_search_view
                WHERE (:district IS NULL OR district = :district)
                ORDER BY overall_score DESC NULLS LAST, registration_date DESC NULLS LAST
                LIMIT 5;
                """
            ),
        ),
        (
            "High location_score projects",
            dedent(
                """
                SELECT project_id, project_name, district, tehsil, location_score, geo_confidence
                FROM project_search_view
                WHERE location_score >= 70
                ORDER BY location_score DESC NULLS LAST
                LIMIT 5;
                """
            ),
        ),
        (
            "Recent registrations",
            dedent(
                """
                SELECT project_id, project_name, district, tehsil, registration_date, overall_score
                FROM project_search_view
                WHERE registration_date IS NOT NULL
                ORDER BY registration_date DESC
                LIMIT 5;
                """
            ),
        ),
    ]

    for title, sql in examples:
        _print_header(title)
        result = conn.execute(text(sql), params)
        rows = result.mappings().all()
        for row in rows:
            print(dict(row))
        if not rows:
            print("(no rows)")


def explain_bbox(conn) -> None:
    _print_header("BBox query plan (lat/lon filter)")
    plan_sql = dedent(
        """
        EXPLAIN (FORMAT TEXT)
        SELECT project_id, project_name, lat, lon, overall_score
        FROM project_search_view
        WHERE lat BETWEEN 20 AND 23 AND lon BETWEEN 80 AND 83
        ORDER BY overall_score DESC NULLS LAST
        LIMIT 20;
        """
    )
    plan_rows = conn.execute(text(plan_sql)).scalars().all()
    for line in plan_rows:
        print(line)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--district", help="Optional district filter for examples", default=None)
    args = parser.parse_args()

    engine = get_engine()
    with engine.connect() as conn:
        inspect_counts(conn)
        run_sample_queries(conn, args.district)
        explain_bbox(conn)


if __name__ == "__main__":
    main()
