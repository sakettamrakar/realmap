import pytest
from unittest.mock import MagicMock, patch
from ai.features.builder import build_feature_pack
from ai.scoring.logic import score_project_quality

def test_feature_builder_structure():
    """Test that feature pack builder produces expected JSON structure."""
    # Mock Project
    mock_project = MagicMock()
    mock_project.id = 123
    mock_project.project_name = "Test Project"
    mock_project.state_code = "CG"
    mock_project.district = "Raipur"
    mock_project.tehsil = "Raipur"
    mock_project.status = "ongoing"
    mock_project.approved_date = None
    mock_project.proposed_end_date = None
    mock_project.open_space_area_sqmt = 100.0
    
    # Mock Relationships
    mock_promoter = MagicMock()
    mock_promoter.promoter_name = "Builder A"
    mock_promoter.promoter_type = "Individual"
    mock_project.promoters = [mock_promoter]
    
    mock_stat = MagicMock()
    mock_stat.onsite_available = True
    mock_stat.amenity_type = "Pool"
    mock_stat.nearby_count = 5
    mock_stat.nearby_nearest_km = 0.5
    mock_project.amenity_stats = [mock_stat]
    
    mock_project.documents = []
    mock_project.quarterly_updates = []
    mock_project.latitude = 21.25
    mock_project.longitude = 81.63
    
    # Mock DB Session
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_project
    
    # Run
    snapshot = build_feature_pack(123, db=mock_db)
    
    # Assert
    assert snapshot is not None
    assert snapshot.project_id == 123
    assert snapshot.features["name"] == "Test Project"
    assert snapshot.features["promoters"][0]["name"] == "Builder A"
    assert "Pool" in snapshot.features["amenities"]["onsite"]
    assert snapshot.features["amenities"]["nearby"][0]["type"] == "Pool"
    assert snapshot.features["signals"]["has_lat_lon"] is True

@patch("ai.scoring.logic.run")
def test_scoring_logic(mock_run):
    """Test scoring logic parses LLM response correctly."""
    # Mock LLM response
    mock_run.return_value = {
        "text": '```json\n{"score": 85, "confidence": 0.9, "explanation": "Good", "risks": [], "strengths": []}\n```',
        "tokens_used": 100,
        "latency_ms": 500,
        "error": None
    }
    
    features = {"name": "Test"}
    result = score_project_quality(features)
    
    assert result["score"] == 85
    assert result["confidence"] == 0.9
    assert result["explanation"] == "Good"
    assert result["metadata"]["tokens_used"] == 100
