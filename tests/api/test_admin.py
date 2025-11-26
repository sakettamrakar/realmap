"""Tests for admin/debug API endpoints."""
from __future__ import annotations

import os
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from cg_rera_extractor.api.app import app  # noqa: E402
from cg_rera_extractor.api.deps import get_db  # noqa: E402
from cg_rera_extractor.api.routes_admin import (  # noqa: E402
    _find_project_artifacts,
    _find_file_artifacts,
    _get_amenity_details,
    _get_pricing_details,
    _get_geo_details,
    _get_score_details,
)
from cg_rera_extractor.db import (  # noqa: E402
    Base,
    Project,
    ProjectScores,
    ProjectAmenityStats,
    ProjectLocation,
    ProjectPricingSnapshot,
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
def db_session(session_local: sessionmaker):
    """Get a database session for tests."""
    with session_local() as session:
        yield session


@pytest.fixture()
def api_client(session_local: sessionmaker) -> TestClient:
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


@pytest.fixture
def sample_project(session_local: sessionmaker):
    """Create a project with various related records for testing."""
    with session_local() as session:
        project = Project(
            state_code="CG",
            rera_registration_number="PCGRERA240000001",
            project_name="Test Admin Project",
            status="ongoing",
            district="Raipur",
            tehsil="Raipur",
            village_or_locality="Test Village",
            full_address="123 Test Street, Raipur",
            latitude=21.2514,
            longitude=81.6296,
            geocoding_status="success",
            geocoding_source="nominatim",
            geo_source="nominatim",
            geo_precision="rooftop",
            geo_confidence=0.95,
        )
        session.add(project)
        session.flush()
        
        # Add scores
        score = ProjectScores(
            project_id=project.id,
            amenity_score=75.5,
            location_score=68.0,
            overall_score=72.0,
            value_score=65.0,
            score_status="complete",
            score_version=1,
        )
        session.add(score)
        
        # Add amenity stats - onsite
        onsite_stat = ProjectAmenityStats(
            project_id=project.id,
            amenity_type="gym",
            radius_km=None,
            onsite_available=True,
            onsite_details="Fully equipped gymnasium",
        )
        session.add(onsite_stat)
        
        # Add amenity stats - nearby
        nearby_stat = ProjectAmenityStats(
            project_id=project.id,
            amenity_type="school",
            radius_km=2.0,
            nearby_count=5,
            nearby_nearest_km=0.8,
            onsite_available=False,
        )
        session.add(nearby_stat)
        
        # Add location candidates
        loc1 = ProjectLocation(
            project_id=project.id,
            source_type="nominatim",
            lat=21.2514,
            lon=81.6296,
            precision_level="rooftop",
            confidence_score=0.95,
            is_active=True,
        )
        loc2 = ProjectLocation(
            project_id=project.id,
            source_type="google",
            lat=21.2520,
            lon=81.6300,
            precision_level="approximate",
            confidence_score=0.80,
            is_active=False,
        )
        session.add_all([loc1, loc2])
        
        # Add pricing snapshot
        pricing = ProjectPricingSnapshot(
            project_id=project.id,
            snapshot_date=date(2024, 1, 15),
            unit_type_label="2BHK",
            min_price_total=3500000,
            max_price_total=4500000,
            min_price_per_sqft=4500,
            max_price_per_sqft=5000,
            source_type="manual",
            is_active=True,
        )
        session.add(pricing)
        
        session.commit()
        session.refresh(project)
        
        # Return project id - need to re-fetch in other tests
        return project.id


class TestAdminHelpers:
    """Test helper functions for admin endpoint."""
    
    def test_get_score_details_with_scores(self, session_local: sessionmaker, sample_project: int):
        """Test score details extraction."""
        with session_local() as session:
            project = session.query(Project).filter_by(id=sample_project).first()
            result = _get_score_details(project)
        
        assert result["amenity_score"] == 75.5
        assert result["location_score"] == 68.0
        assert result["overall_score"] == 72.0
        assert result["value_score"] == 65.0
        assert result["score_status"] == "complete"
        assert str(result["score_version"]) == "1"
    
    def test_get_score_details_no_scores(self, session_local: sessionmaker):
        """Test score details when no scores exist."""
        with session_local() as session:
            project = Project(
                state_code="CG",
                rera_registration_number="PCGRERA240000099",
                project_name="No Scores Project",
            )
            session.add(project)
            session.commit()
            session.refresh(project)
            
            result = _get_score_details(project)
            assert result == {"status": "no_scores"}
    
    def test_get_geo_details(self, session_local: sessionmaker, sample_project: int):
        """Test geo details extraction."""
        with session_local() as session:
            project = session.query(Project).filter_by(id=sample_project).first()
            result = _get_geo_details(project)
        
        # Primary location
        assert result["primary"]["lat"] == pytest.approx(21.2514)
        assert result["primary"]["lon"] == pytest.approx(81.6296)
        assert result["primary"]["geocoding_status"] == "success"
        assert result["primary"]["geo_source"] == "nominatim"
        assert result["primary"]["geo_precision"] == "rooftop"
        assert result["primary"]["geo_confidence"] == pytest.approx(0.95)
        
        # Candidate locations
        assert len(result["candidate_locations"]) == 2
        active_loc = next(l for l in result["candidate_locations"] if l["is_active"])
        assert active_loc["source_type"] == "nominatim"
        assert active_loc["lat"] == pytest.approx(21.2514)
    
    def test_get_amenity_details(self, session_local: sessionmaker, sample_project: int):
        """Test amenity details extraction."""
        with session_local() as session:
            project = session.query(Project).filter_by(id=sample_project).first()
            result = _get_amenity_details(project)
        
        # Onsite amenities
        assert len(result["onsite"]) == 1
        assert result["onsite"][0]["amenity_type"] == "gym"
        assert result["onsite"][0]["onsite_available"] is True
        assert result["onsite"][0]["onsite_details"] == "Fully equipped gymnasium"
        
        # Nearby amenities
        assert len(result["nearby"]) == 1
        assert result["nearby"][0]["amenity_type"] == "school"
        assert result["nearby"][0]["radius_km"] == 2.0
        assert result["nearby"][0]["nearby_count"] == 5
        assert result["nearby"][0]["nearby_nearest_km"] == pytest.approx(0.8)
    
    def test_get_pricing_details(self, session_local: sessionmaker, sample_project: int):
        """Test pricing details extraction."""
        with session_local() as session:
            project = session.query(Project).filter_by(id=sample_project).first()
            result = _get_pricing_details(project)
        
        assert len(result["snapshots"]) == 1
        snapshot = result["snapshots"][0]
        assert snapshot["unit_type_label"] == "2BHK"
        assert snapshot["min_price_total"] == 3500000
        assert snapshot["max_price_total"] == 4500000
        assert snapshot["min_price_per_sqft"] == 4500
        assert snapshot["max_price_per_sqft"] == 5000
        assert snapshot["source_type"] == "manual"
        assert snapshot["is_active"] is True
    
    def test_find_project_artifacts(self, session_local: sessionmaker, sample_project: int):
        """Test finding DB artifacts (empty case)."""
        with session_local() as session:
            project = session.query(Project).filter_by(id=sample_project).first()
            result = _find_project_artifacts(project, session)
        
        assert "db_artifacts" in result
        assert isinstance(result["db_artifacts"], list)
    
    def test_find_file_artifacts_nonexistent(self):
        """Test finding file artifacts for nonexistent RERA."""
        result = _find_file_artifacts("NONEXISTENT_RERA_NUMBER")
        
        assert "scraped_json" in result
        assert "raw_html" in result
        assert "raw_extracted" in result
        assert "previews" in result
        assert "listings" in result
        # All should be empty for nonexistent RERA
        assert len(result["scraped_json"]) == 0


class TestAdminEndpoints:
    """Test admin API endpoints via test client."""
    
    def test_full_debug_endpoint(self, api_client: TestClient, session_local: sessionmaker, sample_project: int):
        """Test the full_debug endpoint returns expected structure."""
        response = api_client.get(f"/admin/projects/{sample_project}/full_debug")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check top-level structure
        assert "core" in data
        assert "promoters" in data
        assert "detail" in data
        assert "debug" in data
        assert "_meta" in data
        
        # Check core info
        assert data["core"]["id"] == sample_project
        assert data["core"]["rera_registration_number"] == "PCGRERA240000001"
        assert data["core"]["project_name"] == "Test Admin Project"
        
        # Check debug section
        assert "scores_detail" in data["debug"]
        assert "geo_detail" in data["debug"]
        assert "amenities_detail" in data["debug"]
        assert "pricing_detail" in data["debug"]
        assert "db_artifacts" in data["debug"]
        assert "file_artifacts" in data["debug"]
        
        # Check meta
        assert data["_meta"]["project_id"] == sample_project
        assert data["_meta"]["rera_number"] == "PCGRERA240000001"
    
    def test_full_debug_endpoint_not_found(self, api_client: TestClient):
        """Test full_debug with nonexistent project."""
        response = api_client.get("/admin/projects/999999/full_debug")
        assert response.status_code == 404
    
    def test_search_by_rera_endpoint(self, api_client: TestClient, session_local: sessionmaker, sample_project: int):
        """Test searching for project by RERA number."""
        # Full match
        response = api_client.get("/admin/projects/search_by_rera/PCGRERA240000001")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == sample_project
        assert data["rera_registration_number"] == "PCGRERA240000001"
        assert data["project_name"] == "Test Admin Project"
        
        # Partial match
        response = api_client.get("/admin/projects/search_by_rera/240000001")
        assert response.status_code == 200
        assert response.json()["project_id"] == sample_project
    
    def test_search_by_rera_not_found(self, api_client: TestClient):
        """Test search by RERA with no match."""
        response = api_client.get("/admin/projects/search_by_rera/NONEXISTENT")
        assert response.status_code == 404
