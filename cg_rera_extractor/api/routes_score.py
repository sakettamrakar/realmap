from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

router = APIRouter()

class ScoreRequest(BaseModel):
    project_id: str

class ScoreResponse(BaseModel):
    task_id: str
    status: str

@router.post("/score/project", response_model=ScoreResponse)
async def score_project(request: ScoreRequest, background_tasks: BackgroundTasks):
    # Dispatch the task to Celery
    from cg_rera_extractor.worker import score_project_task
    task = score_project_task.delay(request.project_id)
    
    return ScoreResponse(task_id=task.id, status="queued")
