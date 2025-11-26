"""FastAPI application exposing read-only project endpoints."""
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from cg_rera_extractor.api.deps import get_db
from cg_rera_extractor.api.routes_projects import router as projects_router
from cg_rera_extractor.api.routes_admin import router as admin_router
from cg_rera_extractor.api.schemas import ProjectDetail, ProjectSummary
from cg_rera_extractor.db import Project

app = FastAPI(title="CG RERA Projects API", version="0.1.0")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)
app.include_router(admin_router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    """Simple readiness probe."""

    return {"status": "ok"}


@app.get("/projects", response_model=list[ProjectSummary])
def list_projects(
    *,
    district: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[ProjectSummary]:
    """List projects with optional filters and pagination."""

    stmt = select(Project)

    if district:
        stmt = stmt.where(Project.district.ilike(district))

    if status:
        stmt = stmt.where(Project.status.ilike(status))

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Project.project_name.ilike(pattern),
                Project.rera_registration_number.ilike(pattern),
            )
        )

    stmt = stmt.order_by(Project.project_name).offset(offset).limit(limit)

    projects = db.execute(stmt).scalars().all()
    return [ProjectSummary.model_validate(project) for project in projects]


@app.get("/projects/{state_code}/{rera_registration_number}", response_model=ProjectDetail)
def get_project_detail(
    state_code: str,
    rera_registration_number: str,
    db: Session = Depends(get_db),
) -> ProjectDetail:
    """Return a single project's details by registration number."""

    stmt = (
        select(Project)
        .where(
            Project.state_code == state_code,
            Project.rera_registration_number == rera_registration_number,
        )
        .options(
            selectinload(Project.promoters),
            selectinload(Project.buildings),
            selectinload(Project.unit_types),
            selectinload(Project.documents),
            selectinload(Project.quarterly_updates),
        )
    )

    project = db.execute(stmt).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectDetail.model_validate(project)


__all__ = ["app"]
