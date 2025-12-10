import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from ai.main import app
from ai.schemas import AIScoreResponse

client = TestClient(app)

@patch("ai.features.builder.build_feature_pack")
@patch("ai.scoring.logic.score_project_quality")
@patch("cg_rera_extractor.db.get_session_local") # Mock session dependency at source? 
# Depends() overrides need app.dependency_overrides usually
def test_score_project_endpoint(mock_db_getter, mock_score, mock_build):
    """Test end-to-end score endpoint (with mocked logic/db)."""
    
    # Mock Dependencies
    mock_build.return_value = MagicMock(features={"name": "Test"})
    mock_score.return_value = {
        "score": 88, 
        "confidence": 0.8, 
        "explanation": "Test explanation",
        "metadata": {}
    }
    
    # Override DB dependency
    mock_session = MagicMock()
    # Mock row return for INSERT
    mock_session.execute.return_value.fetchone.return_value = [101] 
    
    app.dependency_overrides["get_session_local"] = lambda: mock_session
    
    # Run
    response = client.post("/ai/score/project/1")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["score_value"] == 88.0
    assert data["score_id"] == 101
    
    # Verify DB calls
    assert mock_session.execute.called
    assert mock_session.commit.called
    
    # Cleanup
    app.dependency_overrides = {}
