"""Integration-style tests for the FastAPI project endpoints."""
from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from cg_rera_extractor.api.app import app  # noqa: E402  (import after env setup)
from cg_rera_extractor.api.deps import get_db  # noqa: E402
from cg_rera_extractor.db import (
    Building,
    Project,
    ProjectDocument,
    Promoter,
    QuarterlyUpdate,
    UnitType,
)
from cg_rera_extractor.db.base import Base


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


def seed_projects(session_local: sessionmaker) -> None:
    with session_local() as session:
        project = Project(
            state_code="CG",
            rera_registration_number="CG-001",
            project_name="Skyline Heights",
            district="Raipur",
            status="Ongoing",
            latitude=21.2511,
            longitude=81.6298,
            approved_date=date(2023, 1, 1),
            raw_data_json={"source": "test"},
        )
        project.promoters.append(
            Promoter(
                promoter_name="ACME Developers",
                promoter_type="Company",
                email="info@acme.test",
                phone="1234567890",
            )
        )
        project.buildings.append(
            Building(
                building_name="Tower A",
                building_type="Residential",
                number_of_floors=12,
                total_units=120,
            )
        )
        project.unit_types.append(
            UnitType(
                type_name="2BHK",
                carpet_area_sqmt=Decimal("75.5"),
                saleable_area_sqmt=Decimal("90.0"),
                total_units=60,
                sale_price=Decimal("4500000"),
            )
        )
        project.documents.append(
            ProjectDocument(
                doc_type="Approval", description="Layout Approval", url="http://example.com/doc.pdf"
            )
        )
        project.quarterly_updates.append(
            QuarterlyUpdate(
                quarter="Q1", update_date=date(2024, 1, 15), status="On Track", summary="Foundation complete"
            )
        )

        second = Project(
            state_code="CG",
            rera_registration_number="CG-002",
            project_name="Lake View Residency",
            district="Bilaspur",
            status="Completed",
        )

        session.add_all([project, second])
        session.commit()


def test_healthcheck(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_projects_listing_with_filters(session_local: sessionmaker, client: TestClient) -> None:
    seed_projects(session_local)

    response = client.get("/projects", params={"district": "Raipur"})
    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["project_name"] == "Skyline Heights"

    search_response = client.get("/projects", params={"q": "Lake"})
    assert search_response.status_code == 200
    assert len(search_response.json()) == 1
    assert search_response.json()[0]["rera_registration_number"] == "CG-002"


def test_project_detail_endpoint(session_local: sessionmaker, client: TestClient) -> None:
    seed_projects(session_local)

    response = client.get("/projects/CG/CG-001")
    assert response.status_code == 200
    payload = response.json()

    assert payload["project_name"] == "Skyline Heights"
    assert len(payload["promoters"]) == 1
    assert len(payload["buildings"]) == 1
    assert len(payload["unit_types"]) == 1
    assert len(payload["documents"]) == 1
    assert len(payload["quarterly_updates"]) == 1
