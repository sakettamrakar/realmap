"""Phase 6 end-to-end smoke test covering DB → read model → API."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable, Sequence

from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.orm import Session, selectinload

from cg_rera_extractor.api.app import app
from cg_rera_extractor.api.services import fetch_map_projects, fetch_project_detail, search_projects
from cg_rera_extractor.api.services.search import SearchParams, _resolve_location, _score_to_float
from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
from cg_rera_extractor.db import Project, ProjectScores, get_engine, get_session_local


@dataclass
class TableCheck:
    name: str
    present: bool
    missing_columns: Sequence[str]


@dataclass
class ProjectProbe:
    project_id: int
    name: str
    district: str | None
    tehsil: str | None
    location: tuple[float | None, float | None, str | None]
    scores: dict[str, float | None]
    onsite_count: int
    nearby_types: int
    detail_loaded: bool
    detail_missing: list[str]
    map_pin_count: int


REQUIRED_TABLES: dict[str, Sequence[str]] = {
    "projects": [
        "id",
        "project_name",
        "district",
        "latitude",
        "longitude",
        "geo_precision",
    ],
    "project_scores": ["overall_score", "location_score", "amenity_score", "score_version"],
    "project_amenity_stats": ["amenity_type", "radius_km", "onsite_available", "nearby_count"],
    "project_locations": ["lat", "lon", "precision_level", "is_active"],
}


def check_schema(engine) -> list[TableCheck]:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    checks: list[TableCheck] = []

    for table, expected_cols in REQUIRED_TABLES.items():
        present = table in table_names
        missing_columns: list[str] = []
        if present:
            existing_cols = {col["name"] for col in inspector.get_columns(table)}
            missing_columns = sorted(set(expected_cols) - existing_cols)
        else:
            missing_columns = list(expected_cols)
        checks.append(TableCheck(name=table, present=present, missing_columns=missing_columns))

    return checks


def pick_sample_projects(session: Session, limit: int = 5) -> list[Project]:
    stmt = (
        session.query(Project)
        .options(
            selectinload(Project.score),
            selectinload(Project.amenity_stats),
            selectinload(Project.locations),
        )
        .join(ProjectScores)
        .filter(Project.district.is_not(None))
        .order_by(Project.district, Project.project_name)
        .limit(60)
    )

    candidates = stmt.all()
    by_district: dict[str, Project] = {}
    for project in candidates:
        if project.district and project.district not in by_district:
            lat, lon, _ = _resolve_location(project)
            if lat is None or lon is None:
                continue
            scores = project.score
            if scores is None or scores.overall_score is None:
                continue
            by_district[project.district] = project
            if len(by_district) >= limit:
                break

    return list(by_district.values())[:limit]


def probe_project(session: Session, project: Project, use_api: bool, client: TestClient | None) -> ProjectProbe:
    lat, lon, quality = _resolve_location(project)
    scores = project.score
    score_block = {
        "overall": _score_to_float(scores.overall_score) if scores else None,
        "location": _score_to_float(scores.location_score) if scores else None,
        "amenity": _score_to_float(scores.amenity_score) if scores else None,
    }

    onsite_count = sum(
        1 for stat in project.amenity_stats if stat.radius_km is None and stat.onsite_available
    )
    nearby_types = len({stat.amenity_type for stat in project.amenity_stats if stat.radius_km is not None})

    detail_payload = fetch_project_detail(session, project.id)
    detail_missing: list[str] = []
    if detail_payload:
        if detail_payload["scores"]["overall_score"] is None:
            detail_missing.append("overall_score")
        if detail_payload["location"]["lat"] is None or detail_payload["location"]["lon"] is None:
            detail_missing.append("lat/lon")
        amenities = detail_payload.get("amenities", {})
        onsite_list = amenities.get("onsite_list", [])
        nearby_summary = amenities.get("nearby_summary", {})
        if onsite_list and not nearby_summary:
            detail_missing.append("nearby_context")
    else:
        detail_missing.append("detail_not_found")

    bbox = None
    map_pin_count = 0
    if lat is not None and lon is not None:
        delta = 0.1
        bbox = (lat - delta, lon - delta, lat + delta, lon + delta)
        pins = fetch_map_projects(session, bbox=bbox, min_overall_score=0)
        map_pin_count = len(pins)

    if use_api and client and bbox:
        client.get("/health")
        client.get(f"/projects/{project.id}")
        client.get(
            "/projects/search",
            params={
                "district": project.district,
                "sort_by": "overall_score",
                "page_size": 3,
            },
        )
        client.get(
            "/projects/map",
            params={
                "bbox": ",".join(str(round(coord, 4)) for coord in bbox),
                "min_overall_score": 0,
            },
        )

    return ProjectProbe(
        project_id=project.id,
        name=project.project_name,
        district=project.district,
        tehsil=project.tehsil,
        location=(lat, lon, quality),
        scores=score_block,
        onsite_count=onsite_count,
        nearby_types=nearby_types,
        detail_loaded=detail_payload is not None,
        detail_missing=detail_missing,
        map_pin_count=map_pin_count,
    )


def search_scenario(session: Session, project: Project) -> dict[str, float | int | str | None]:
    params = SearchParams(district=project.district, sort_by="overall_score", sort_dir="desc", page_size=5)
    total, items = search_projects(session, params)
    top_score = items[0]["overall_score"] if items else None
    trailing_score = items[-1]["overall_score"] if items else None
    sorted_ok = all(
        items[i]["overall_score"] >= items[i + 1]["overall_score"]
        for i in range(len(items) - 1)
        if items[i]["overall_score"] is not None and items[i + 1]["overall_score"] is not None
    )
    seen_project = any(item["project_id"] == project.id for item in items)
    return {
        "district": project.district,
        "total": total,
        "top_score": top_score,
        "trailing_score": trailing_score,
        "sorted_ok": sorted_ok,
        "contains_sample": seen_project,
    }


def report_schema(checks: Iterable[TableCheck]) -> None:
    print("\nDB schema")
    print("---------")
    for check in checks:
        status = "OK" if check.present and not check.missing_columns else "WARN"
        missing = f" missing={','.join(check.missing_columns)}" if check.missing_columns else ""
        print(f"- {check.name:22} : {status}{missing}")


def report_project(probe: ProjectProbe) -> None:
    lat, lon, quality = probe.location
    score_str = ", ".join(f"{k}={v}" for k, v in probe.scores.items())
    print(
        f"• [{probe.project_id}] {probe.name} ({probe.district}/{probe.tehsil}) | "
        f"scores: {score_str} | geo: {lat},{lon} ({quality})"
    )
    print(
        f"    onsite={probe.onsite_count} nearby_types={probe.nearby_types} "
        f"detail={'ok' if probe.detail_loaded else 'missing'} missing={probe.detail_missing or 'none'} "
        f"map_pins={probe.map_pin_count}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=4, help="Number of districts/projects to probe")
    parser.add_argument(
        "--skip-api", action="store_true", help="Skip FastAPI TestClient checks (DB-only mode)"
    )
    args = parser.parse_args()

    ensure_database_url()
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    session = SessionLocal()

    client = TestClient(app) if not args.skip_api else None

    print("Phase 6 Smoke Test")
    print("===================")
    print(f"Database: {describe_database_target(engine.url)}")

    schema_checks = check_schema(engine)
    report_schema(schema_checks)

    projects = pick_sample_projects(session, limit=args.limit)
    if not projects:
        print("No projects with scores and geo data found.")
        return 1

    print("\nSample projects")
    print("---------------")
    for project in projects:
        probe = probe_project(session, project, use_api=not args.skip_api, client=client)
        report_project(probe)

    print("\nSearch scenarios")
    print("----------------")
    for project in projects[:2]:
        scenario = search_scenario(session, project)
        print(
            f"- district={scenario['district']} total={scenario['total']} "
            f"sorted_ok={scenario['sorted_ok']} contains_sample={scenario['contains_sample']} "
            f"top={scenario['top_score']} tail={scenario['trailing_score']}"
        )

    print("\nMap spot-checks")
    print("---------------")
    for project in projects[:2]:
        lat, lon, _ = _resolve_location(project)
        if lat is None or lon is None:
            continue
        bbox = (lat - 0.2, lon - 0.2, lat + 0.2, lon + 0.2)
        pins = fetch_map_projects(session, bbox=bbox, min_overall_score=0)
        print(
            f"- {project.district}: bbox=({bbox[0]:.3f},{bbox[1]:.3f})-({bbox[2]:.3f},{bbox[3]:.3f}) "
            f"pins={len(pins)}"
        )

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
