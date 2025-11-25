"""Quality checks for amenity stats and project scores."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
from cg_rera_extractor.db import (
    Project,
    ProjectAmenityStats,
    ProjectScores,
    get_engine,
    get_session_local,
)


@dataclass
class StatsSummary:
    count: int
    min: float | None
    mean: float | None
    max: float | None


def summarize(values: Iterable[float | int | None]) -> StatsSummary:
    numeric_values = [float(v) for v in values if v is not None]
    if not numeric_values:
        return StatsSummary(count=0, min=None, mean=None, max=None)
    return StatsSummary(
        count=len(numeric_values),
        min=min(numeric_values),
        mean=round(mean(numeric_values), 2),
        max=max(numeric_values),
    )


def pct(part: int, whole: int) -> float:
    return round((part / whole) * 100, 2) if whole else 0.0


def fetch_project_counts(session: Session) -> dict[str, int]:
    total_projects = session.scalar(select(func.count(Project.id))) or 0
    with_coords = (
        session.scalar(
            select(func.count(Project.id)).where(
                Project.latitude.is_not(None), Project.longitude.is_not(None)
            )
        )
        or 0
    )
    with_stats = (
        session.scalar(select(func.count(func.distinct(ProjectAmenityStats.project_id))))
        or 0
    )
    with_scores = (
        session.scalar(select(func.count(func.distinct(ProjectScores.project_id)))) or 0
    )

    return {
        "total_projects": total_projects,
        "with_coordinates": with_coords,
        "with_stats": with_stats,
        "with_scores": with_scores,
    }


def amenity_distribution(session: Session) -> dict[str, dict[str, Any]]:
    per_type: dict[str, list[float]] = defaultdict(list)
    stmt: Select[Any] = select(
        ProjectAmenityStats.amenity_type, ProjectAmenityStats.nearby_count
    )
    for amenity_type, count in session.execute(stmt):
        if count is None:
            continue
        per_type[amenity_type].append(count)

    return {key: asdict(summarize(values)) for key, values in sorted(per_type.items())}


def score_distribution(session: Session) -> dict[str, StatsSummary]:
    summaries = {}
    for field in ["overall_score", "amenity_score", "location_score"]:
        col = getattr(ProjectScores, field)
        stmt = select(col).where(col.is_not(None))
        summaries[field] = summarize(value for value, in session.execute(stmt))
    return summaries


def sample_projects(
    session: Session, stmt: Select[Any], limit: int
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in session.execute(stmt.limit(limit)):
        rows.append(
            {
                "project_id": row.id,
                "registration": f"{row.state_code}-{row.rera_registration_number}",
                "name": row.project_name,
            }
        )
    return rows


def anomalies(
    session: Session,
    *,
    sample_size: int,
    poi_threshold: int,
    radius_km: float,
) -> dict[str, Any]:
    missing_stats_stmt = (
        select(Project.id, Project.state_code, Project.rera_registration_number, Project.project_name)
        .where(Project.latitude.is_not(None), Project.longitude.is_not(None))
        .where(~Project.id.in_(select(ProjectAmenityStats.project_id)))
        .order_by(Project.id)
    )

    stats_no_scores_stmt = (
        select(Project.id, Project.state_code, Project.rera_registration_number, Project.project_name)
        .join(ProjectAmenityStats)
        .where(~Project.id.in_(select(ProjectScores.project_id)))
        .group_by(Project.id, Project.state_code, Project.rera_registration_number, Project.project_name)
        .order_by(Project.id)
    )

    weird_values_stmt = (
        select(
            ProjectAmenityStats.project_id,
            ProjectAmenityStats.amenity_type,
            ProjectAmenityStats.radius_km,
            ProjectAmenityStats.nearby_count,
        )
        .where(ProjectAmenityStats.nearby_count.is_not(None))
        .where(ProjectAmenityStats.nearby_count > poi_threshold)
        .where(ProjectAmenityStats.radius_km <= radius_km)
        .order_by(ProjectAmenityStats.project_id)
    )

    missing_stats_count = (
        session.scalar(select(func.count()).select_from(missing_stats_stmt.subquery()))
        or 0
    )
    stats_no_scores_count = (
        session.scalar(select(func.count()).select_from(stats_no_scores_stmt.subquery()))
        or 0
    )
    weird_values_count = (
        session.scalar(select(func.count()).select_from(weird_values_stmt.subquery())) or 0
    )

    weird_samples: list[dict[str, Any]] = []
    for project_id, amenity_type, radius, count in session.execute(
        weird_values_stmt.limit(sample_size)
    ):
        weird_samples.append(
            {
                "project_id": project_id,
                "amenity_type": amenity_type,
                "radius_km": float(radius),
                "count_within_radius": count,
            }
        )

    return {
        "projects_with_coords_no_stats": {
            "count": missing_stats_count,
            "sample": sample_projects(session, missing_stats_stmt, sample_size),
        },
        "stats_without_scores": {
            "count": stats_no_scores_count,
            "sample": sample_projects(session, stats_no_scores_stmt, sample_size),
        },
        "suspicious_poi_counts": {
            "count": weird_values_count,
            "threshold": poi_threshold,
            "radius_km": radius_km,
            "sample": weird_samples,
        },
    }


def print_summary(report: dict[str, Any]) -> None:
    metrics = report["metrics"]
    score_summaries: dict[str, StatsSummary] = report["score_distribution"]
    print("\n==== AMENITY & SCORE QA ====")
    print(f"Database: {report['database']}")
    print(f"Generated: {report['generated_at']}")
    print()
    print(f"Total projects:             {metrics['total_projects']}")
    print(
        f"With coordinates:          {metrics['with_coordinates']} "
        f"({pct(metrics['with_coordinates'], metrics['total_projects'])}%)"
    )
    print(
        f"With amenity stats:        {metrics['with_stats']} "
        f"({pct(metrics['with_stats'], metrics['with_coordinates'])}% of geocoded)"
    )
    print(
        f"With scores:               {metrics['with_scores']} "
        f"({pct(metrics['with_scores'], metrics['with_stats'])}% of stats)"
    )
    print()
    print("Score distributions:")
    for name, summary in score_summaries.items():
        print(
            f"  {name:<18}: count={summary.count}, min={summary.min}, "
            f"mean={summary.mean}, max={summary.max}"
        )

    print("\nAmenity POI distributions (count_within_radius):")
    for amenity_type, summary_dict in report["amenity_distribution"].items():
        print(
            f"  {amenity_type:>18}: "
            f"count={summary_dict['count']}, min={summary_dict['min']}, "
            f"mean={summary_dict['mean']}, max={summary_dict['max']}"
        )

    print("\nAnomalies and gaps:")
    anomalies_block: dict[str, Any] = report["anomalies"]
    coords_gap = anomalies_block["projects_with_coords_no_stats"]
    print(
        f"  Projects with coords but no stats: {coords_gap['count']} "
        f"(sample {len(coords_gap['sample'])})"
    )
    stats_no_scores = anomalies_block["stats_without_scores"]
    print(
        f"  Projects with stats but no scores: {stats_no_scores['count']} "
        f"(sample {len(stats_no_scores['sample'])})"
    )
    weird = anomalies_block["suspicious_poi_counts"]
    print(
        f"  Suspicious POI counts (> {weird['threshold']} within {weird['radius_km']} km): "
        f"{weird['count']} (sample {len(weird['sample'])})"
    )
    print()

    def _print_sample(title: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        print(title)
        for row in rows:
            reg = row.get("registration") or row.get("project_id")
            name = row.get("name")
            print(f"    [{reg}] {name}")

    _print_sample("Sample missing stats:", coords_gap["sample"])
    _print_sample("Sample stats without scores:", stats_no_scores["sample"])
    if weird["sample"]:
        print("Sample suspicious POI counts:")
        for row in weird["sample"]:
            print(
                "    "
                f"project={row['project_id']}, type={row['amenity_type']}, "
                f"radius_km={row['radius_km']}, count={row['count_within_radius']}"
            )
    print()


def write_report(output_path: Path, report: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run QA checks for amenity stats and scores"
    )
    parser.add_argument(
        "--output-json",
        default="runs/amenity_qa_report.json",
        help="Path to write JSON report (set to empty to skip)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5,
        help="Number of sample projects to include per anomaly bucket",
    )
    parser.add_argument(
        "--poi-threshold",
        type=int,
        default=100,
        help="Counts above this value within the radius will be flagged as suspicious",
    )
    parser.add_argument(
        "--radius-km",
        type=float,
        default=1.0,
        help="Only stats at or below this radius are inspected for suspicious POI counts",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Skip writing the JSON report to disk",
    )
    args = parser.parse_args()

    db_url = ensure_database_url()
    engine = get_engine()
    SessionLocal = get_session_local(engine)

    with SessionLocal() as session:
        metrics = fetch_project_counts(session)
        amenity_dist = amenity_distribution(session)
        score_dist = score_distribution(session)
        anomaly_block = anomalies(
            session,
            sample_size=args.sample_size,
            poi_threshold=args.poi_threshold,
            radius_km=args.radius_km,
        )

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "database": describe_database_target(db_url),
        "metrics": metrics,
        "amenity_distribution": amenity_dist,
        "score_distribution": {k: asdict(v) for k, v in score_dist.items()},
        "anomalies": anomaly_block,
        "parameters": {
            "sample_size": args.sample_size,
            "poi_threshold": args.poi_threshold,
            "radius_km": args.radius_km,
        },
    }

    print_summary({**report, "score_distribution": score_dist})

    if not args.no_write and args.output_json:
        write_report(Path(args.output_json), report)
        print(f"Report written to {args.output_json}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
