from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
import os

from ai.schemas import HealthCheck, AIScoreResponse
from ai.dependencies import get_db

app = FastAPI(
    title="RealMap AI Microservice",
    description="Dedicated microservice for AI scoring and enrichment",
    version="0.1.0",
    docs_url="/ai/docs",
    openapi_url="/ai/openapi.json"
)

# Feature Flags
AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"
AI_SCORE_ENABLED = os.getenv("AI_SCORE_ENABLED", "true").lower() == "true"

@app.get("/ai/health", response_model=HealthCheck)
async def health_check():
    """Service health check."""
    return {
        "status": "ok" if AI_ENABLED else "disabled",
        "model_loaded": False, # TODO: Connect to LLM adapter status
        "version": "0.1.0"
    }

@app.post("/ai/score/project/{project_id}", response_model=AIScoreResponse)
async def score_project(project_id: int, db: Session = Depends(get_db)):
    """
    Trigger AI scoring for a specific project.
    """
    if not AI_ENABLED or not AI_SCORE_ENABLED:
        raise HTTPException(status_code=503, detail="AI services are currently disabled")
    
    # 1. Load project features
    from ai.features.builder import build_feature_pack
    snapshot = build_feature_pack(project_id, db=db)
    
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
    # 2. Call LLM Scoring
    from ai.scoring.logic import score_project_quality
    result = score_project_quality(snapshot.features)
    
    # 3. Save result (using raw SQL for decoupled safety or ORM if model existed)
    # Using raw SQL to match the "create table in migration" approach
    from sqlalchemy import text
    import json
    from datetime import datetime
    
    model_name = "llama-local-v1" # TODO: Get from adapter
    
    try:
        # Insert into ai_scores
        stmt = text("""
            INSERT INTO ai_scores 
            (project_id, model_name, model_version, score_value, confidence, explanation, input_features, provenance) 
            VALUES (:pid, :mname, :mver, :val, :conf, :expl, :feat, :prov) 
            RETURNING id
        """)
        
        row = db.execute(stmt, {
            "pid": project_id,
            "mname": model_name,
            "mver": "1.0",
            "val": result["score"],
            "conf": result["confidence"],
            "expl": result["explanation"],
            "feat": json.dumps(snapshot.features),
            "prov": json.dumps(result.get("metadata", {}))
        }).fetchone()
        
        new_score_id = row[0]
        
        # Update project pointer
        db.execute(text("UPDATE projects SET latest_ai_score_id = :sid WHERE id = :pid"), {
            "sid": new_score_id,
            "pid": project_id
        })
        
        db.commit()
        
        return {
            "score_id": new_score_id,
            "project_id": project_id,
            "score_value": float(result["score"]),
            "confidence": float(result["confidence"]),
            "explanation": result["explanation"],
            "model_name": model_name,
            "created_at": datetime.utcnow()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/ai/score/{score_id}", response_model=AIScoreResponse)
async def get_score(score_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific score details."""
    if not AI_ENABLED:
        raise HTTPException(status_code=503, detail="AI services are currently disabled")
    
    from sqlalchemy import text
    row = db.execute(text("SELECT id, project_id, score_value, confidence, explanation, model_name, created_at FROM ai_scores WHERE id = :sid"), {"sid": score_id}).fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Score not found")
        
    return {
        "score_id": row.id,
        "project_id": row.project_id,
        "score_value": float(row.score_value) if row.score_value is not None else 0.0,
        "confidence": float(row.confidence) if row.confidence is not None else 0.0,
        "explanation": row.explanation,
        "model_name": row.model_name,
        "created_at": row.created_at
    }

@app.post("/ai/extract/rera", response_model=bool)
async def extract_rera_doc(file_path: str, project_id: int, db: Session = Depends(get_db)):
    """
    Trigger RERA document extraction for a specific file.
    """
    if not AI_ENABLED:
        raise HTTPException(status_code=503, detail="AI services are currently disabled")
        
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    from ai.rera.parser import ReraPdfParser
    
    try:
        parser = ReraPdfParser(use_ocr=True) # or config driven
        result = parser.process_file(file_path, project_id=project_id, db=db)
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Feature 6: Chat Search ============
from pydantic import BaseModel
from typing import List, Optional

class ChatSearchRequest(BaseModel):
    query: str
    limit: int = 5

class ChatSearchProject(BaseModel):
    id: int
    name: Optional[str]
    location: Optional[str]
    score: float

class ChatSearchResponse(BaseModel):
    query: str
    answer: str
    projects: List[ChatSearchProject]
    success: bool

@app.post("/api/v1/chat/search", response_model=ChatSearchResponse)
async def chat_search(request: ChatSearchRequest, db: Session = Depends(get_db)):
    """
    Natural language search for projects.
    Feature 6: AI Chat Assistant.
    """
    if not AI_ENABLED:
        raise HTTPException(status_code=503, detail="AI services are currently disabled")
    
    from ai.chat.assistant import ChatAssistant
    
    try:
        assistant = ChatAssistant(db)
        result = assistant.answer(request.query, limit=request.limit)
        
        return ChatSearchResponse(
            query=result["query"],
            answer=result["answer"],
            projects=[ChatSearchProject(**p) for p in result["projects"]],
            success=result["success"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat search failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

