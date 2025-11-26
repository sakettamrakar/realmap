"""Tests for the score explanation helper."""
from __future__ import annotations

import os
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from cg_rera_extractor.analysis.explain import explain_project_score
from cg_rera_extractor.db.base import Base
from cg_rera_extractor.db.models import Project, ProjectAmenityStats, ProjectScores


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


def seed_project_with_good_scores(session_local: sessionmaker) -> int:
    """Seed a project with good location and amenity data."""
    with session_local() as session:
        project = Project(
            state_code="CG",
            rera_registration_number="CG-TEST-001",
            project_name="Test Heights",
            district="Raipur",
            status="Ongoing",
            latitude=Decimal("21.2511"),
            longitude=Decimal("81.6298"),
        )
        session.add(project)
        session.flush()
        
        # Add scores
        scores = ProjectScores(
            project_id=project.id,
            amenity_score=Decimal("65.0"),
            location_score=Decimal("78.0"),
            overall_score=Decimal("71.5"),
            connectivity_score=70,
            daily_needs_score=80,
            social_infra_score=75,
            score_status="ok",
            score_status_reason=None,
            score_version="amenity_v1",
        )
        session.add(scores)
        
        # Add onsite amenities (some strong, some weak)
        onsite_amenities = [
            ("internal_roads", True, {"progress": 0.85}),
            ("water_supply", True, {"progress": 0.75}),
            ("clubhouse", True, {"progress": 0.20}),
            ("park", True, {"progress": 0.15}),
            ("parking", True, None),
        ]
        
        for amenity_type, available, details in onsite_amenities:
            stat = ProjectAmenityStats(
                project_id=project.id,
                amenity_type=amenity_type,
                radius_km=None,
                onsite_available=available,
                onsite_details=details,
            )
            session.add(stat)
        
        # Add nearby/location context stats
        nearby_stats = [
            ("school", 3.0, 4, Decimal("0.8")),
            ("hospital", 5.0, 1, Decimal("6.5")),
            ("grocery_convenience", 2.0, 3, Decimal("0.5")),
            ("transit_stop", 3.0, 5, Decimal("1.2")),
        ]
        
        for amenity_type, radius, count, nearest in nearby_stats:
            stat = ProjectAmenityStats(
                project_id=project.id,
                amenity_type=amenity_type,
                radius_km=Decimal(str(radius)),
                nearby_count=count,
                nearby_nearest_km=nearest,
            )
            session.add(stat)
        
        session.commit()
        return project.id


def seed_project_with_insufficient_data(session_local: sessionmaker) -> int:
    """Seed a project with insufficient data for scoring."""
    with session_local() as session:
        project = Project(
            state_code="CG",
            rera_registration_number="CG-TEST-002",
            project_name="Sparse Project",
            district="Bilaspur",
            status="Ongoing",
        )
        session.add(project)
        session.flush()
        
        scores = ProjectScores(
            project_id=project.id,
            overall_score=None,
            score_status="insufficient_data",
            score_status_reason=["missing_nearby_data", "missing_onsite_data"],
            score_version="amenity_v1",
        )
        session.add(scores)
        session.commit()
        return project.id


def seed_project_without_scores(session_local: sessionmaker) -> int:
    """Seed a project without any score record."""
    with session_local() as session:
        project = Project(
            state_code="CG",
            rera_registration_number="CG-TEST-003",
            project_name="No Score Project",
            district="Durg",
            status="Pending",
        )
        session.add(project)
        session.commit()
        return project.id


class TestExplainProjectScore:
    """Tests for explain_project_score function."""
    
    def test_explain_project_with_good_data(self, session_local: sessionmaker) -> None:
        """Test explanation generation for a project with good data."""
        project_id = seed_project_with_good_scores(session_local)
        
        with session_local() as session:
            explanation = explain_project_score(project_id, session)
        
        assert "summary" in explanation
        assert "positives" in explanation
        assert "negatives" in explanation
        assert "factors" in explanation
        
        # Should have a meaningful summary
        assert explanation["summary"] != ""
        assert "location" in explanation["summary"].lower() or "infrastructure" in explanation["summary"].lower()
        
        # Should have some positives (schools, transit, roads, water)
        assert len(explanation["positives"]) > 0
        
        # Should have some negatives (hospital distance, clubhouse/park progress)
        assert len(explanation["negatives"]) > 0
        
        # Check factors structure
        assert "onsite" in explanation["factors"]
        assert "location" in explanation["factors"]
        assert "strong" in explanation["factors"]["onsite"]
        assert "weak" in explanation["factors"]["onsite"]
        assert "strong" in explanation["factors"]["location"]
        assert "weak" in explanation["factors"]["location"]
        
        # Internal roads and water supply should be strong (>=70% progress)
        assert "internal_roads" in explanation["factors"]["onsite"]["strong"]
        assert "water_supply" in explanation["factors"]["onsite"]["strong"]
        
        # Clubhouse and park should be weak (<30% progress)
        assert "clubhouse" in explanation["factors"]["onsite"]["weak"]
        assert "park" in explanation["factors"]["onsite"]["weak"]
        
        # Schools should be strong (4 schools is >= 3 threshold)
        assert "school" in explanation["factors"]["location"]["strong"]
        
        # Hospital should be weak (only 1 and far away)
        assert "hospital" in explanation["factors"]["location"]["weak"]
    
    def test_explain_project_with_insufficient_data(self, session_local: sessionmaker) -> None:
        """Test explanation for a project with insufficient scoring data."""
        project_id = seed_project_with_insufficient_data(session_local)
        
        with session_local() as session:
            explanation = explain_project_score(project_id, session)
        
        assert explanation["summary"] == "Not enough data to explain score"
        assert len(explanation["positives"]) == 0
        assert len(explanation["negatives"]) > 0
        
        # The negatives should mention the missing data
        negatives_text = " ".join(explanation["negatives"]).lower()
        assert "missing" in negatives_text or "data" in negatives_text
    
    def test_explain_project_without_scores(self, session_local: sessionmaker) -> None:
        """Test explanation for a project without any score record."""
        project_id = seed_project_without_scores(session_local)
        
        with session_local() as session:
            explanation = explain_project_score(project_id, session)
        
        # Should handle gracefully
        assert explanation["summary"] == "Not enough data to explain score"
        assert len(explanation["positives"]) == 0
        assert len(explanation["negatives"]) > 0
    
    def test_explain_nonexistent_project(self, session_local: sessionmaker) -> None:
        """Test explanation for a project that doesn't exist."""
        with session_local() as session:
            explanation = explain_project_score(999999, session)
        
        assert "not found" in explanation["summary"].lower()
        assert len(explanation["negatives"]) > 0
    
    def test_explanation_is_json_serializable(self, session_local: sessionmaker) -> None:
        """Verify the explanation can be serialized to JSON."""
        import json
        
        project_id = seed_project_with_good_scores(session_local)
        
        with session_local() as session:
            explanation = explain_project_score(project_id, session)
        
        # Should not raise
        json_str = json.dumps(explanation)
        assert json_str is not None
        
        # Should round-trip correctly
        parsed = json.loads(json_str)
        assert parsed == explanation
    
    def test_positives_and_negatives_limited_to_three(self, session_local: sessionmaker) -> None:
        """Verify that positives and negatives are limited to at most 3 items."""
        project_id = seed_project_with_good_scores(session_local)
        
        with session_local() as session:
            explanation = explain_project_score(project_id, session)
        
        assert len(explanation["positives"]) <= 3
        assert len(explanation["negatives"]) <= 3
