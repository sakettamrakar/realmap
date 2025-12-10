from unittest.mock import MagicMock, patch
from ai.features.builder import build_feature_pack
from ai.scoring.logic import score_project_quality
import ai.llm.adapter

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


# LLM Adapter Tests
def test_llm_run_without_model():
    """Test LLM run returns response when model not available."""
    # Without model, should return response with ai_unavailable error
    result = ai.llm.adapter.run(prompt="Test prompt")
    
    assert result["text"] != ""
    assert "tokens_used" in result
    assert "latency_ms" in result
    assert result["error"] == "ai_unavailable"  # Model not loaded


@patch("ai.llm.adapter.get_llm_instance")
def test_run_llm_success(mock_get_llm):
    """Test successful LLM execution."""
    # Mock LLM instance
    mock_llm = MagicMock()
    mock_llm.return_value = {
        "choices": [{"text": "Generated response"}],
        "usage": {"total_tokens": 150}
    }
    mock_get_llm.return_value = mock_llm
    
    result = ai.llm.adapter.run(prompt="Test prompt", max_tokens=500)
    
    assert result["text"] == "Generated response"
    assert result["tokens_used"] == 150
    assert result["error"] is None
    assert "latency_ms" in result


@patch("ai.llm.adapter.get_llm_instance")
def test_run_llm_execution_error(mock_get_llm):
    """Test LLM run when execution fails."""
    mock_llm = MagicMock()
    mock_llm.side_effect = Exception("CUDA out of memory")
    mock_get_llm.return_value = mock_llm
    
    result = ai.llm.adapter.run(prompt="Test prompt")
    
    # Should return empty text with error message
    assert result["text"] == ""
    assert result["error"] == "CUDA out of memory"
    assert "latency_ms" in result


@patch("ai.scoring.logic.run")
def test_scoring_with_malformed_json(mock_run):
    """Test scoring logic handles malformed LLM responses."""
    # Mock LLM response with invalid JSON
    mock_run.return_value = {
        "text": 'This is not valid JSON',
        "tokens_used": 50,
        "latency_ms": 300,
        "error": None
    }
    
    features = {"name": "Test"}
    result = score_project_quality(features)
    
    # Should return fallback/default values
    assert "score" in result
    assert "confidence" in result
    assert "explanation" in result


def test_feature_builder_with_no_amenities():
    """Test feature builder with project that has no amenity stats."""
    mock_project = MagicMock()
    mock_project.id = 456
    mock_project.project_name = "Minimal Project"
    mock_project.state_code = "CG"
    mock_project.district = "Durg"
    mock_project.tehsil = "Durg"
    mock_project.status = "completed"
    mock_project.approved_date = None
    mock_project.proposed_end_date = None
    mock_project.open_space_area_sqmt = None
    mock_project.promoters = []
    mock_project.amenity_stats = []
    mock_project.documents = []
    mock_project.quarterly_updates = []
    mock_project.latitude = None
    mock_project.longitude = None
    
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_project
    
    snapshot = build_feature_pack(456, db=mock_db)
    
    assert snapshot is not None
    assert snapshot.project_id == 456
    assert snapshot.features["amenities"]["onsite"] == []
    assert snapshot.features["amenities"]["nearby"] == []
    assert snapshot.features["signals"]["has_lat_lon"] is False


def test_feature_builder_project_not_found():
    """Test feature builder returns None when project doesn't exist."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    snapshot = build_feature_pack(999, db=mock_db)
    
    assert snapshot is None
