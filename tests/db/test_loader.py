"""Tests for the V1 JSON loader into the database."""
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from cg_rera_extractor.db.base import Base
from cg_rera_extractor.db.loader import load_run_into_db
from cg_rera_extractor.db.models import Building, Project, ProjectDocument, Promoter, QuarterlyUpdate, UnitType


def _make_session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    return SessionLocal()


def _write_v1_fixture(path: Path, *, registration: str, project_name: str, promoter_name: str) -> None:
    data = {
        "metadata": {"schema_version": "1.0", "state_code": "CG", "scraped_at": "2024-01-01T00:00:00Z"},
        "project_details": {
            "registration_number": registration,
            "project_name": project_name,
            "project_status": "Registered",
            "district": "Raipur",
            "tehsil": "Raipur",
            "project_address": "123 Test Street",
            "launch_date": "2024-01-15",
            "expected_completion_date": "2025-06-30",
        },
        "promoter_details": [
            {
                "name": promoter_name,
                "organisation_type": "Company",
                "email": "info@example.com",
                "phone": "1234567890",
                "address": "Promoter Address",
            }
        ],
        "building_details": [
            {"name": "Tower A", "number_of_floors": 10, "number_of_units": 80, "carpet_area_sq_m": 75.5}
        ],
        "unit_types": [
            {"name": "2BHK", "carpet_area_sq_m": 70.0, "built_up_area_sq_m": 85.0, "price_in_inr": 5500000.0}
        ],
        "documents": [{"name": "Approval", "document_type": "Approval", "url": "http://example.com/doc.pdf"}],
        "quarterly_updates": [
            {"quarter": "Q1", "year": "2024", "status": "On Track", "completion_percent": 10.0, "remarks": "Started"}
        ],
        "raw_data": {"sections": {}, "unmapped_sections": {}},
        "validation_messages": [],
    }
    path.write_text(json.dumps(data))


def test_load_run_into_db_idempotent(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001" / "scraped_json"
    run_dir.mkdir(parents=True)

    v1_path = run_dir / "project.v1.json"
    _write_v1_fixture(v1_path, registration="CG-123", project_name="First Pass", promoter_name="Alpha Builders")

    session = _make_session(tmp_path)

    first_stats = load_run_into_db(str(run_dir.parent), session=session)
    assert first_stats["projects_upserted"] == 1
    assert first_stats["promoters"] == 1
    assert first_stats["buildings"] == 1
    assert first_stats["unit_types"] == 1
    assert first_stats["documents"] == 1
    assert first_stats["quarterly_updates"] == 1

    project = session.execute(
        select(Project).where(Project.rera_registration_number == "CG-123")
    ).scalar_one()
    assert project.project_name == "First Pass"
    assert project.approved_date.isoformat() == "2024-01-15"
    assert project.proposed_end_date.isoformat() == "2025-06-30"
    assert session.query(Promoter).count() == 1
    assert session.query(Building).count() == 1
    assert session.query(UnitType).count() == 1
    assert session.query(ProjectDocument).count() == 1
    assert session.query(QuarterlyUpdate).count() == 1

    _write_v1_fixture(v1_path, registration="CG-123", project_name="Updated Name", promoter_name="Beta Builders")
    second_stats = load_run_into_db(str(run_dir.parent), session=session)
    assert second_stats["projects_upserted"] == 1
    assert session.query(Project).count() == 1
    project = session.execute(
        select(Project).where(Project.rera_registration_number == "CG-123")
    ).scalar_one()
    assert project.project_name == "Updated Name"
    assert session.query(Promoter).count() == 1
    assert session.query(Promoter).one().promoter_name == "Beta Builders"
