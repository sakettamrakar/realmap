"""Quality checks for geocoding results stored in the database."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
from cg_rera_extractor.db import Project, get_engine, get_session_local

INDIA_BOUNDS = {
    "min_lat": 6.0,
    "max_lat": 38.0,
    "min_lon": 68.0,
    "max_lon": 98.0,
}


def to_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return None


def pct(part: int, whole: int) -> float:
    return round((part / whole) * 100, 2) if whole else 0.0


def build_sample_row(row: Any, lat: float | None, lon: float | None) -> dict[str, Any]:
    return {
        "id": row.id,
        "registration": f"{row.state_code}-{row.rera_registration_number}",
        "name": row.project_name,
        "district": row.district,
        "latitude": lat,
        "longitude": lon,
        "geocoding_status": row.geocoding_status,
    }


def evaluate_projects(
    session: Session, sample_size: int, bounds: dict[str, float]
) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "total_projects": 0,
        "with_coordinates": 0,
        "missing_coordinates": 0,
        "missing_latitude": 0,
        "missing_longitude": 0,
        "out_of_bounds": 0,
        "missing_normalized_address": 0,
        "geocoding_status": {},
    }

    samples: dict[str, list[dict[str, Any]]] = {
        "missing_coordinates": [],
        "out_of_bounds": [],
        "missing_normalized_address": [],
    }

    stmt = select(
        Project.id,
        Project.state_code,
        Project.rera_registration_number,
        Project.project_name,
        Project.district,
        Project.latitude,
        Project.longitude,
        Project.geocoding_status,
        Project.raw_data_json,
        Project.full_address,
    )

    for row in session.execute(stmt):
        metrics["total_projects"] += 1
        lat = to_float(row.latitude)
        lon = to_float(row.longitude)
        coords_present = lat is not None and lon is not None

        if coords_present:
            metrics["with_coordinates"] += 1
        else:
            metrics["missing_coordinates"] += 1
            if lat is None:
                metrics["missing_latitude"] += 1
            if lon is None:
                metrics["missing_longitude"] += 1
            if len(samples["missing_coordinates"]) < sample_size:
                samples["missing_coordinates"].append(build_sample_row(row, lat, lon))

        if coords_present:
            out_of_bounds = (
                (lat < bounds["min_lat"])
                or (lat > bounds["max_lat"])
                or (lon < bounds["min_lon"])
                or (lon > bounds["max_lon"])
            )
            if out_of_bounds:
                metrics["out_of_bounds"] += 1
                if len(samples["out_of_bounds"]) < sample_size:
                    samples["out_of_bounds"].append(build_sample_row(row, lat, lon))

        normalized_address = None
        if isinstance(row.raw_data_json, dict):
            normalized_address = row.raw_data_json.get("normalized_address")
            if not normalized_address:
                normalized_address = row.raw_data_json.get("normalizedAddress")
        if not normalized_address:
            normalized_address = row.full_address
        if not normalized_address:
            metrics["missing_normalized_address"] += 1
            if len(samples["missing_normalized_address"]) < sample_size:
                samples["missing_normalized_address"].append(
                    build_sample_row(row, lat, lon)
                )

        status = row.geocoding_status or "UNSET"
        metrics["geocoding_status"][status] = metrics["geocoding_status"].get(status, 0) + 1

    metrics["coverage_pct"] = pct(metrics["with_coordinates"], metrics["total_projects"])
    metrics["out_of_bounds_pct"] = pct(
        metrics["out_of_bounds"], metrics["with_coordinates"]
    )
    metrics["missing_normalized_address_pct"] = pct(
        metrics["missing_normalized_address"], metrics["total_projects"]
    )

    return {"metrics": metrics, "samples": samples}


def print_summary(report: dict[str, Any]) -> None:
    metrics = report["metrics"]
    bounds = report["bounds"]
    print("\n==== GEO QA SUMMARY ====")
    print(f"Database: {report['database']}")
    print(f"Generated: {report['generated_at']}")
    print(
        "Bounding box: "
        f"lat {bounds['min_lat']}–{bounds['max_lat']}, "
        f"lon {bounds['min_lon']}–{bounds['max_lon']}"
    )
    print()
    print(f"Total projects:            {metrics['total_projects']}")
    print(
        f"With coordinates:         {metrics['with_coordinates']} "
        f"({metrics['coverage_pct']}%)"
    )
    print(f"Missing latitude:          {metrics['missing_latitude']}")
    print(f"Missing longitude:         {metrics['missing_longitude']}")
    print(
        f"Out of bounds (India):     {metrics['out_of_bounds']} "
        f"({metrics['out_of_bounds_pct']}% of geocoded)"
    )
    print(
        f"Missing normalized addr:   {metrics['missing_normalized_address']} "
        f"({metrics['missing_normalized_address_pct']}%)"
    )
    print()
    print("Geocoding status distribution:")
    for status, count in sorted(metrics["geocoding_status"].items()):
        print(f"  {status:>12}: {count}")

    for key, rows in report["samples"].items():
        print(f"\nSample: {key.replace('_', ' ').title()} (showing {len(rows)})")
        for row in rows:
            coords = (
                f"lat={row['latitude']}, lon={row['longitude']}"
                if row["latitude"] is not None and row["longitude"] is not None
                else "no coords"
            )
            print(
                f"  [{row['id']}] {row['registration']} | {row['name']} | "
                f"{row['district']} | {coords}"
            )
    print()


def write_report(output_path: Path, report: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run GEO QA checks against the database")
    parser.add_argument(
        "--output-json",
        default="runs/geo_qa_report.json",
        help="Path to write the JSON report (default: runs/geo_qa_report.json). Use --no-write to disable writing.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5,
        help="Number of sample projects to include for each issue category",
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
        evaluation = evaluate_projects(session, args.sample_size, INDIA_BOUNDS)

    report = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "database": describe_database_target(db_url),
        "bounds": INDIA_BOUNDS,
        **evaluation,
    }

    print_summary(report)

    if not args.no_write and args.output_json:
        write_report(Path(args.output_json), report)
        print(f"Report written to {args.output_json}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
