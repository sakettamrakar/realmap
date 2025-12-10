"""
Gated Access API Routes (Point 14).

Secure document access with lead capture.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from cg_rera_extractor.api.deps import get_db
from cg_rera_extractor.api.schemas_api import (
    BrochureAccessRequest,
    BrochureAccessResponse,
)
from cg_rera_extractor.api.services.access import process_brochure_access

router = APIRouter(prefix="/access", tags=["access"])


@router.post("/brochure", response_model=BrochureAccessResponse)
def request_brochure_access(
    *,
    request: BrochureAccessRequest,
    db=Depends(get_db),
):
    """
    Request access to a project brochure (Lead-Wall Flow).
    
    This endpoint implements a lead capture mechanism before providing
    download access. Users must provide contact information and consent
    to receive a time-limited download link.
    
    ## Flow
    1. User submits email/phone and consent
    2. Lead is captured for CRM/marketing
    3. A signed URL is generated (valid for 15 minutes)
    4. User can download the brochure using the signed URL
    
    ## Security
    - Direct brochure URLs are never exposed
    - Signed URLs expire after 15 minutes
    - Download count is limited per token
    - All access is logged for analytics
    
    ## Request Body
    ```json
    {
        "project_id": 123,
        "document_id": null,  // Optional, defaults to main brochure
        "email": "user@example.com",
        "phone": "+919876543210",
        "name": "John Doe",
        "marketing_consent": true,
        "privacy_consent": true,
        "utm_source": "google",
        "utm_medium": "cpc"
    }
    ```
    
    ## Response
    On success:
    ```json
    {
        "success": true,
        "signed_url": {
            "download_url": "/api/v1/download?doc_id=456&expires=...",
            "expires_at": "2024-01-15T10:15:00Z",
            "expires_in_seconds": 900,
            "document_id": 456,
            "filename": "project_brochure.pdf",
            "file_format": "pdf",
            "access_token": "...",
            "download_limit": 3
        },
        "lead_id": "abc123..."
    }
    ```
    
    On failure:
    ```json
    {
        "success": false,
        "error_code": "CONTACT_REQUIRED",
        "error_message": "Email or phone number is required"
    }
    ```
    """
    result = process_brochure_access(db, request)
    
    # If critical error (not just missing brochure), raise HTTP exception
    if not result.success and result.error_code in ("PROJECT_NOT_FOUND",):
        raise HTTPException(
            status_code=404,
            detail=result.error_message,
        )
    
    if not result.success and result.error_code in ("CONSENT_REQUIRED", "CONTACT_REQUIRED"):
        raise HTTPException(
            status_code=400,
            detail=result.error_message,
        )
    
    return result


@router.get("/brochure/{project_id}/available")
def check_brochure_availability(
    project_id: int,
    db=Depends(get_db),
):
    """
    Check if a brochure is available for a project.
    
    Use this endpoint before showing the download button to users.
    Does not require authentication or lead capture.
    
    ## Response
    ```json
    {
        "available": true,
        "document_count": 2,
        "formats": ["pdf", "docx"]
    }
    ```
    """
    from cg_rera_extractor.db import Project, ProjectDocument, ProjectArtifact
    
    # Check project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Count available brochures
    doc_count = (
        db.query(ProjectDocument)
        .filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.doc_type.ilike("%brochure%"),
        )
        .count()
    )
    
    artifact_count = (
        db.query(ProjectArtifact)
        .filter(
            ProjectArtifact.project_id == project_id,
            ProjectArtifact.artifact_type.ilike("%brochure%"),
        )
        .count()
    )
    
    total = doc_count + artifact_count
    
    # Get formats
    formats = set()
    docs = (
        db.query(ProjectDocument.url)
        .filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.doc_type.ilike("%brochure%"),
        )
        .all()
    )
    for (url,) in docs:
        if url and "." in url:
            formats.add(url.split(".")[-1].lower())
    
    artifacts = (
        db.query(ProjectArtifact.file_format)
        .filter(
            ProjectArtifact.project_id == project_id,
            ProjectArtifact.artifact_type.ilike("%brochure%"),
        )
        .all()
    )
    for (fmt,) in artifacts:
        if fmt:
            formats.add(fmt.lower())
    
    return {
        "available": total > 0,
        "document_count": total,
        "formats": list(formats) if formats else ["pdf"],
    }


__all__ = ["router"]
