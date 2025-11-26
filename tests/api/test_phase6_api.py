from __future__ import annotations

import os
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from cg_rera_extractor.api.app import app  # noqa: E402
from cg_rera_extractor.api.deps import get_db  # noqa: E402
from cg_rera_extractor.db import (  # noqa: E402
    Base,
    Project,
    ProjectAmenityStats,
    ProjectLocation,
    ProjectScores,
)


@pytest.fixture()
def session_local() -> sessionmaker:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture()
def client(session_local: sessionmaker) -> TestClient:
    def _get_db():
        db = session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def seed_phase6(session_local: sessionmaker) -> tuple[int, int]:
    with session_local() as session:
        project = Project(
            state_code="CG",
            rera_registration_number="CG-100",
            project_name="Phase6 Heights",
            district="Raipur",
            tehsil="Raipur",
            status="Registered",
            latitude=21.2511,
            longitude=81.6298,
            approved_date=date(2023, 3, 1),
        )
        project.score = ProjectScores(
            amenity_score=80,
            location_score=70,
            overall_score=75,
            score_version="v1",
        )
        project.amenity_stats.append(
            ProjectAmenityStats(amenity_type="clubhouse", onsite_available=True, radius_km=None)
        )
        project.amenity_stats.append(
            ProjectAmenityStats(amenity_type="schools", nearby_count=3, nearby_nearest_km=2.1, radius_km=5)
        )
        project.locations.append(
            ProjectLocation(source_type="geocoder", lat=21.2511, lon=81.6298, precision_level="rooftop", is_active=True)
        )

        second = Project(
            state_code="CG",
            rera_registration_number="CG-200",
            project_name="Canal Residency",
            district="Durg",
            tehsil="Patan",
            status="Ongoing",
            latitude=21.19,
            longitude=81.28,
            approved_date=date(2022, 6, 1),
        )
        second.score = ProjectScores(overall_score=60, location_score=55, amenity_score=50, score_version="v1")

        session.add_all([project, second])
        session.commit()
        return project.id, second.id


def test_search_endpoint(client: TestClient, session_local: sessionmaker) -> None:
    project_id, second_id = seed_phase6(session_local)

    response = client.get("/projects/search")
    assert response.status_code == 200
    payload = response.json()

    assert payload["total"] == 2
    assert len(payload["items"]) == 2
    assert {item["project_id"] for item in payload["items"]} == {project_id, second_id}


def test_search_by_district(client: TestClient, session_local: sessionmaker) -> None:
    project_id, _ = seed_phase6(session_local)

    response = client.get("/projects/search", params={"district": "Raipur"})
    assert response.status_code == 200
    payload = response.json()

    assert payload["total"] == 1
    assert payload["items"][0]["project_id"] == project_id
    assert "clubhouse" in payload["items"][0]["highlight_amenities"]


def test_project_detail_endpoint(client: TestClient, session_local: sessionmaker) -> None:
    project_id, _ = seed_phase6(session_local)

    response = client.get(f"/projects/{project_id}")
    assert response.status_code == 200
    payload = response.json()

    assert payload["project"]["project_id"] == project_id
    assert payload["scores"]["overall_score"] == 75.0  # Scores are returned in 0-100 range
    assert "onsite_list" in payload["amenities"]
    
    # Verify score_explanation is present
    assert "score_explanation" in payload
    assert "summary" in payload["score_explanation"]
    assert "positives" in payload["score_explanation"]
    assert "negatives" in payload["score_explanation"]


def test_map_endpoint_bbox(client: TestClient, session_local: sessionmaker) -> None:
    first_id, _ = seed_phase6(session_local)

    response = client.get("/projects/map", params={"bbox": "20.0,80.0,22.0,82.0"})
    assert response.status_code == 200
    payload = response.json()

    assert len(payload["items"]) >= 1
    assert any(item["project_id"] == first_id for item in payload["items"])
