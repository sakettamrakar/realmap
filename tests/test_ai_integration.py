from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from ai.main import app
from ai.dependencies import get_db

client = TestClient(app)


@patch("ai.features.builder.build_feature_pack")
@patch("ai.scoring.logic.score_project_quality")
def test_score_project_endpoint_success(mock_score, mock_build):
    """Test successful scoring of a project."""
    
    # Mock Dependencies
    mock_build.return_value = MagicMock(features={"name": "Test"})
    mock_score.return_value = {
        "score": 88, 
        "confidence": 0.8, 
        "explanation": "Test explanation",
        "metadata": {}
    }
    
    # Override DB dependency with mock session
    mock_session = MagicMock()
    # Mock row return for INSERT - needs to be a tuple-like object with attribute access
    mock_row = MagicMock()
    mock_row.__getitem__ = lambda self, key: 101  # For row[0] access
    mock_session.execute.return_value.fetchone.return_value = mock_row
    
    def override_get_db():
        yield mock_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Run
    response = client.post("/ai/score/project/1")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["score_value"] == 88.0
    assert data["score_id"] == 101
    assert data["project_id"] == 1
    assert data["confidence"] == 0.8
    assert data["explanation"] == "Test explanation"
    assert "created_at" in data
    
    # Verify DB calls
    assert mock_session.execute.called
    assert mock_session.commit.called
    
    # Cleanup
    app.dependency_overrides = {}


@patch("ai.features.builder.build_feature_pack")
def test_score_project_not_found(mock_build):
    """Test 404 when project is not found."""
    
    # Mock build_feature_pack to return None (project not found)
    mock_build.return_value = None
    
    mock_session = MagicMock()
    
    def override_get_db():
        yield mock_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Run
    response = client.post("/ai/score/project/999")
    
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
    # Cleanup
    app.dependency_overrides = {}


@patch("ai.features.builder.build_feature_pack")
@patch("ai.scoring.logic.score_project_quality")
def test_score_project_database_error(mock_score, mock_build):
    """Test 500 when database error occurs."""
    
    # Mock Dependencies
    mock_build.return_value = MagicMock(features={"name": "Test"})
    mock_score.return_value = {
        "score": 88, 
        "confidence": 0.8, 
        "explanation": "Test",
        "metadata": {}
    }
    
    # Mock session to raise exception on execute
    mock_session = MagicMock()
    mock_session.execute.side_effect = Exception("Database connection failed")
    
    def override_get_db():
        yield mock_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Run
    response = client.post("/ai/score/project/1")
    
    # Assert
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]
    assert mock_session.rollback.called
    
    # Cleanup
    app.dependency_overrides = {}


def test_get_score_success():
    """Test successful retrieval of a score."""
    
    # Create mock row with attribute access
    mock_row = MagicMock()
    mock_row.id = 101
    mock_row.project_id = 1
    mock_row.score_value = 88.5
    mock_row.confidence = 0.85
    mock_row.explanation = "High quality project"
    mock_row.model_name = "llama-local-v1"
    mock_row.created_at = "2025-12-10T10:00:00"
    
    mock_session = MagicMock()
    mock_session.execute.return_value.fetchone.return_value = mock_row
    
    def override_get_db():
        yield mock_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Run
    response = client.get("/ai/score/101")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["score_id"] == 101
    assert data["project_id"] == 1
    assert data["score_value"] == 88.5
    assert data["confidence"] == 0.85
    assert data["explanation"] == "High quality project"
    
    # Cleanup
    app.dependency_overrides = {}


def test_get_score_not_found():
    """Test 404 when score is not found."""
    
    mock_session = MagicMock()
    mock_session.execute.return_value.fetchone.return_value = None
    
    def override_get_db():
        yield mock_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Run
    response = client.get("/ai/score/999")
    
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
    # Cleanup
    app.dependency_overrides = {}


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/ai/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert "version" in data
    assert data["version"] == "0.1.0"
