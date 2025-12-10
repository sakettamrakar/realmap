"""
Gated Brochure Access Service (Point 14).

Implements lead-wall flow with time-limited signed URLs.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from cg_rera_extractor.db import Project, ProjectDocument, ProjectArtifact
from cg_rera_extractor.api.schemas_api import (
    BrochureAccessRequest,
    BrochureAccessResponse,
    SignedUrlResponse,
)


# Configuration - in production, these should come from environment/config
SIGNING_SECRET = "your-secret-key-change-in-production"  # TODO: Move to config
SIGNED_URL_EXPIRY_SECONDS = 900  # 15 minutes
MAX_DOWNLOADS_PER_TOKEN = 3
BASE_DOWNLOAD_URL = "/api/v1/download"  # Internal download endpoint


class LeadCaptureService:
    """
    Handles lead capture and storage.
    
    In production, this would integrate with a CRM system.
    """
    
    @staticmethod
    def capture_lead(request: BrochureAccessRequest, db: Session) -> str | None:
        """
        Capture lead information and return a lead ID.
        
        Returns None if lead capture fails validation.
        """
        # Validate at least one contact method
        if not request.email and not request.phone:
            return None
        
        # In production: Store to CRM, send to webhook, etc.
        # For now, generate a simple lead ID
        lead_data = f"{request.email or ''}{request.phone or ''}{time.time()}"
        lead_id = hashlib.sha256(lead_data.encode()).hexdigest()[:16]
        
        # TODO: Store lead in database or send to CRM
        # lead = Lead(
        #     lead_id=lead_id,
        #     email=request.email,
        #     phone=request.phone,
        #     name=request.name,
        #     project_id=request.project_id,
        #     marketing_consent=request.marketing_consent,
        #     utm_source=request.utm_source,
        #     utm_medium=request.utm_medium,
        #     utm_campaign=request.utm_campaign,
        # )
        # db.add(lead)
        # db.commit()
        
        return lead_id


class SignedUrlGenerator:
    """
    Generates time-limited signed URLs for secure document access.
    
    Similar to AWS S3 presigned URLs but for internal use.
    """
    
    def __init__(self, secret: str = SIGNING_SECRET):
        self.secret = secret.encode()
    
    def generate_access_token(self) -> str:
        """Generate a unique access token for tracking."""
        return secrets.token_urlsafe(32)
    
    def sign_url(
        self,
        document_id: int,
        file_path: str,
        expiry_seconds: int = SIGNED_URL_EXPIRY_SECONDS,
    ) -> tuple[str, datetime, str]:
        """
        Generate a signed URL with expiry.
        
        Returns: (signed_url, expires_at, access_token)
        """
        access_token = self.generate_access_token()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expiry_seconds)
        expires_timestamp = int(expires_at.timestamp())
        
        # Create signature payload
        payload = f"{document_id}:{file_path}:{expires_timestamp}:{access_token}"
        signature = hmac.new(
            self.secret,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Build signed URL
        params = {
            "doc_id": document_id,
            "expires": expires_timestamp,
            "token": access_token,
            "sig": signature,
        }
        signed_url = f"{BASE_DOWNLOAD_URL}?{urlencode(params)}"
        
        return signed_url, expires_at, access_token
    
    def verify_signature(
        self,
        document_id: int,
        file_path: str,
        expires_timestamp: int,
        access_token: str,
        signature: str,
    ) -> bool:
        """Verify a signed URL signature."""
        payload = f"{document_id}:{file_path}:{expires_timestamp}:{access_token}"
        expected_signature = hmac.new(
            self.secret,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)


def get_brochure_document(
    db: Session,
    project_id: int,
    document_id: int | None = None,
) -> tuple[ProjectDocument | ProjectArtifact | None, str | None]:
    """
    Find the brochure document for a project.
    
    Returns: (document, file_path)
    """
    # If specific document requested
    if document_id:
        doc = (
            db.query(ProjectDocument)
            .filter(
                ProjectDocument.id == document_id,
                ProjectDocument.project_id == project_id,
            )
            .first()
        )
        if doc:
            return doc, doc.url
        
        # Try artifacts table
        artifact = (
            db.query(ProjectArtifact)
            .filter(
                ProjectArtifact.id == document_id,
                ProjectArtifact.project_id == project_id,
            )
            .first()
        )
        if artifact:
            return artifact, artifact.file_path or artifact.source_url
    
    # Find any brochure for this project
    # Check documents first
    brochure_doc = (
        db.query(ProjectDocument)
        .filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.doc_type.ilike("%brochure%"),
        )
        .first()
    )
    if brochure_doc:
        return brochure_doc, brochure_doc.url
    
    # Check artifacts
    brochure_artifact = (
        db.query(ProjectArtifact)
        .filter(
            ProjectArtifact.project_id == project_id,
            ProjectArtifact.artifact_type.ilike("%brochure%"),
        )
        .first()
    )
    if brochure_artifact:
        return brochure_artifact, brochure_artifact.file_path or brochure_artifact.source_url
    
    return None, None


def process_brochure_access(
    db: Session,
    request: BrochureAccessRequest,
) -> BrochureAccessResponse:
    """
    Process a brochure access request.
    
    1. Validate the request
    2. Capture lead information
    3. Find the document
    4. Generate signed URL
    5. Return response
    """
    # Validate project exists
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        return BrochureAccessResponse(
            success=False,
            error_code="PROJECT_NOT_FOUND",
            error_message=f"Project {request.project_id} not found",
        )
    
    # Validate contact information
    if not request.email and not request.phone:
        return BrochureAccessResponse(
            success=False,
            error_code="CONTACT_REQUIRED",
            error_message="Email or phone number is required",
        )
    
    # Validate consent
    if not request.privacy_consent:
        return BrochureAccessResponse(
            success=False,
            error_code="CONSENT_REQUIRED",
            error_message="Privacy policy consent is required",
        )
    
    # Find the brochure
    document, file_path = get_brochure_document(db, request.project_id, request.document_id)
    if not document or not file_path:
        return BrochureAccessResponse(
            success=False,
            error_code="BROCHURE_NOT_FOUND",
            error_message="No brochure available for this project",
        )
    
    # Capture lead
    lead_service = LeadCaptureService()
    lead_id = lead_service.capture_lead(request, db)
    
    # Generate signed URL
    url_generator = SignedUrlGenerator()
    signed_url, expires_at, access_token = url_generator.sign_url(
        document_id=document.id,
        file_path=file_path,
        expiry_seconds=SIGNED_URL_EXPIRY_SECONDS,
    )
    
    # Determine file metadata
    filename = file_path.split("/")[-1] if "/" in file_path else file_path
    file_format = filename.split(".")[-1].lower() if "." in filename else "pdf"
    
    # Get filesize if available (would need actual file access)
    filesize_kb = None
    if hasattr(document, "filesize_kb"):
        filesize_kb = document.filesize_kb
    
    return BrochureAccessResponse(
        success=True,
        signed_url=SignedUrlResponse(
            download_url=signed_url,
            expires_at=expires_at,
            expires_in_seconds=SIGNED_URL_EXPIRY_SECONDS,
            document_id=document.id,
            filename=filename,
            file_format=file_format,
            filesize_kb=filesize_kb,
            access_token=access_token,
            download_limit=MAX_DOWNLOADS_PER_TOKEN,
        ),
        lead_id=lead_id,
    )


__all__ = [
    "process_brochure_access",
    "SignedUrlGenerator",
    "LeadCaptureService",
    "get_brochure_document",
]
