from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime

class HealthCheck(BaseModel):
    status: str
    model_loaded: bool
    version: str

class AIScoreRequest(BaseModel):
    # Optional parameters for the scoring run
    model_override: Optional[str] = None
    force_refresh: bool = False

class AIScoreResponse(BaseModel):
    score_id: int
    project_id: int
    score_value: float
    confidence: float
    explanation: str
    model_name: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class FeatureSnapshot(BaseModel):
    project_id: int
    features: Dict[str, Any]

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

class ReraExtractionResult(BaseModel):
    proposed_completion_date: Optional[str] = None
    litigation_count: Optional[int] = 0
    architect_name: Optional[str] = None
