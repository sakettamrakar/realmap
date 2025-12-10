"""
Fix for FastAPI Dependency Injection Issue

This patch addresses the critical blocker preventing integration tests and API functionality.

Problem:
--------
The `get_session_local` function from `cg_rera_extractor.db` requires an `engine` parameter
and returns a `sessionmaker`, not a callable FastAPI dependency.

Solution:
---------
Create a proper FastAPI dependency function that yields database sessions.
"""

from cg_rera_extractor.db import get_engine, get_session_local
from sqlalchemy.orm import Session
from typing import Generator

# Create engine and sessionmaker at module level
_engine = get_engine()
_SessionLocal = get_session_local(_engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.
    
    Yields a database session and ensures it's closed after use.
    
    Usage:
    ------
    ```python
    @app.post("/endpoint")
    async def endpoint(db: Session = Depends(get_db)):
        # Use db session here
        pass
    ```
    """
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Example usage in ai/main.py:
# 
# from fastapi import Depends
# from sqlalchemy.orm import Session
# from ai.dependencies import get_db  # Import this function
# 
# @app.post("/ai/score/project/{project_id}", response_model=AIScoreResponse)
# async def score_project(project_id: int, db: Session = Depends(get_db)):
#     """Trigger AI scoring for a specific project."""
#     ...
