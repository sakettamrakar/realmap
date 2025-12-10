import os
import time
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Celery
# Default to localhost if not found (for local dev without docker networking issues)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ai_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="score_project_task")
def score_project_task(project_id: str):
    """
    Background task to score a project using the AI model.
    """
    print(f"DTO-LOG: Starting scoring task for project_id: {project_id}")
    
    # Simulate processing time
    time.sleep(2)
    
    # TODO: Load Model and Score
    # from cg_rera_extractor.ai.model import load_local_model, score_project_logic
    # result = score_project_logic(project_id)
    
    print(f"DTO-LOG: Finished scoring task for project_id: {project_id}")
    return {"project_id": project_id, "status": "completed", "score": "placeholder"}
