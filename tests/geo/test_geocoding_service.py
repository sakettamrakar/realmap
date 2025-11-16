"""Tests for geocoding batch utilities."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cg_rera_extractor.db import Project
from cg_rera_extractor.db.base import Base
from cg_rera_extractor.geo import GeocodingStatus, geocode_missing_projects


class FakeGeocoder:
    def __init__(self) -> None:
        self.source = "FAKE"

    def geocode_project(self, project: Project):
        if project.project_name == "Geocode Me":
            return 12.345678, 98.765432
        return None


def _make_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def test_geocode_missing_projects_updates_coordinates() -> None:
    SessionLocal = _make_session()

    with SessionLocal() as session:
        needs_coords = Project(
            state_code="CG",
            rera_registration_number="CG-001",
            project_name="Geocode Me",
        )
        still_missing = Project(
            state_code="CG",
            rera_registration_number="CG-002",
            project_name="No Coordinates",
        )
        already_done = Project(
            state_code="CG",
            rera_registration_number="CG-003",
            project_name="Already Geocoded",
            geocoding_status=GeocodingStatus.SUCCESS,
            latitude=10.0,
            longitude=20.0,
            geocoding_source="MANUAL",
        )
        session.add_all([needs_coords, still_missing, already_done])
        session.commit()

        counts = geocode_missing_projects(session, FakeGeocoder())

        refreshed_success = session.get(Project, needs_coords.id)
        refreshed_missing = session.get(Project, still_missing.id)
        refreshed_completed = session.get(Project, already_done.id)

        assert counts == {"processed": 2, "success": 1, "not_geocoded": 1}

        assert refreshed_success.geocoding_status == GeocodingStatus.SUCCESS
        assert refreshed_success.geocoding_source == "FAKE"
        assert float(refreshed_success.latitude) == pytest.approx(12.345678)
        assert float(refreshed_success.longitude) == pytest.approx(98.765432)

        assert refreshed_missing.geocoding_status == GeocodingStatus.NOT_GEOCODED
        assert refreshed_missing.latitude is None
        assert refreshed_missing.longitude is None

        assert refreshed_completed.geocoding_status == GeocodingStatus.SUCCESS
        assert float(refreshed_completed.latitude) == pytest.approx(10.0)
        assert float(refreshed_completed.longitude) == pytest.approx(20.0)
