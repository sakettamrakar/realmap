"""Smoke tests for ORM models using an in-memory SQLite database."""
from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from cg_rera_extractor.db import Building, Project, Promoter
from cg_rera_extractor.db.base import Base


def _make_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def test_project_and_promoter_relationships() -> None:
    SessionLocal = _make_session()

    with SessionLocal() as session:
        project = Project(
            state_code="CG",
            rera_registration_number="CG-123",
            project_name="Test Residency",
            status="Ongoing",
            district="Raipur",
            raw_data_json={"source": "fixture"},
            approved_date=date(2023, 1, 15),
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        promoter = Promoter(
            project_id=project.id,
            promoter_name="ACME Developers",
            promoter_type="Company",
            email="info@example.com",
            phone="1234567890",
        )
        session.add(promoter)
        session.commit()
        session.refresh(promoter)
        session.refresh(project)

        assert promoter.project.id == project.id
        assert project.promoters[0].promoter_name == "ACME Developers"
        assert project.raw_data_json == {"source": "fixture"}


def test_unique_project_key_constraint() -> None:
    SessionLocal = _make_session()

    with SessionLocal() as session:
        first = Project(
            state_code="CG",
            rera_registration_number="CG-123",
            project_name="First",
        )
        duplicate = Project(
            state_code="CG",
            rera_registration_number="CG-123",
            project_name="Duplicate",
        )

        session.add_all([first, duplicate])
        with pytest.raises(IntegrityError):
            session.commit()


def test_building_links_to_project() -> None:
    SessionLocal = _make_session()

    with SessionLocal() as session:
        project = Project(
            state_code="CG",
            rera_registration_number="CG-999",
            project_name="Sky Towers",
        )
        session.add(project)
        session.commit()
        session.refresh(project)

        building = Building(
            project_id=project.id,
            building_name="Tower A",
            number_of_floors=12,
            total_units=120,
        )
        session.add(building)
        session.commit()
        session.refresh(project)

        assert project.buildings[0].building_name == "Tower A"
