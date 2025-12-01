"""
Rich Media API Routes (Point 12).

Returns structured media assets with full metadata.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from cg_rera_extractor.api.deps import get_db
from cg_rera_extractor.api.schemas_api import (
    MediaAsset,
    MediaTypeEnum,
    LicenseTypeEnum,
    ProjectMediaResponse,
)
from cg_rera_extractor.db import Project, ProjectArtifact, ProjectDocument

router = APIRouter(prefix="/projects", tags=["media"])


def _classify_media_type(
    artifact_type: str | None,
    category: str | None,
    file_format: str | None,
) -> MediaTypeEnum:
    """Classify an artifact into a media type."""
    if not artifact_type and not category:
        return MediaTypeEnum.GALLERY
    
    type_lower = (artifact_type or "").lower()
    category_lower = (category or "").lower()
    
    # Check for floorplans
    if "floor" in type_lower or "layout" in type_lower:
        return MediaTypeEnum.FLOORPLAN
    
    # Check for masterplan
    if "master" in type_lower or "site" in type_lower:
        return MediaTypeEnum.MASTERPLAN
    
    # Check for brochure
    if "brochure" in type_lower or "pdf" in (file_format or "").lower():
        return MediaTypeEnum.BROCHURE
    
    # Check for video
    if "video" in type_lower or (file_format or "").lower() in ("mp4", "webm", "avi"):
        return MediaTypeEnum.VIDEO
    
    # Check for virtual tour
    if "tour" in type_lower or "360" in type_lower:
        return MediaTypeEnum.VIRTUAL_TOUR
    
    # Check for elevation
    if "elevation" in type_lower or "facade" in type_lower:
        return MediaTypeEnum.ELEVATION
    
    # Check for amenity
    if "amenity" in type_lower or "amenities" in category_lower:
        return MediaTypeEnum.AMENITY
    
    # Default to gallery
    return MediaTypeEnum.GALLERY


def _get_mime_type(file_format: str | None, url: str | None) -> str | None:
    """Determine MIME type from format or URL."""
    fmt = file_format
    if not fmt and url and "." in url:
        fmt = url.split(".")[-1].lower()
    
    if not fmt:
        return None
    
    fmt = fmt.lower()
    mime_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "svg": "image/svg+xml",
        "pdf": "application/pdf",
        "mp4": "video/mp4",
        "webm": "video/webm",
    }
    
    return mime_map.get(fmt)


def _artifact_to_media_asset(artifact: ProjectArtifact, sort_order: int = 0) -> MediaAsset:
    """Convert a ProjectArtifact to a MediaAsset."""
    url = artifact.source_url or artifact.file_path or ""
    file_format = artifact.file_format
    if not file_format and url and "." in url:
        file_format = url.split(".")[-1].lower()
    
    return MediaAsset(
        id=artifact.id,
        type=_classify_media_type(artifact.artifact_type, artifact.category, file_format),
        url=url,
        thumbnail_url=None,  # TODO: Generate thumbnails
        width_px=None,  # TODO: Extract from metadata
        height_px=None,
        filesize_kb=None,  # TODO: Calculate from file
        file_format=file_format,
        mime_type=_get_mime_type(file_format, url),
        license_type=LicenseTypeEnum.RERA_OFFICIAL,  # Default for RERA documents
        attribution=None,
        unit_type_id=None,  # TODO: Link to unit types
        unit_type_label=None,
        title=artifact.artifact_type,
        description=artifact.category,
        sort_order=sort_order,
        is_primary=artifact.is_preview,
        source_url=artifact.source_url,
        captured_at=None,  # TODO: Track capture time
    )


def _document_to_media_asset(doc: ProjectDocument, sort_order: int = 0) -> MediaAsset:
    """Convert a ProjectDocument to a MediaAsset."""
    url = doc.url or ""
    file_format = None
    if url and "." in url:
        file_format = url.split(".")[-1].lower()
    
    return MediaAsset(
        id=doc.id,
        type=_classify_media_type(doc.doc_type, None, file_format),
        url=url,
        thumbnail_url=None,
        width_px=None,
        height_px=None,
        filesize_kb=None,
        file_format=file_format,
        mime_type=_get_mime_type(file_format, url),
        license_type=LicenseTypeEnum.RERA_OFFICIAL,
        attribution=None,
        unit_type_id=None,
        unit_type_label=None,
        title=doc.description or doc.doc_type,
        description=doc.description,
        sort_order=sort_order,
        is_primary=False,
        source_url=url,
        captured_at=None,
    )


@router.get("/{project_id}/media", response_model=ProjectMediaResponse)
def get_project_media(
    project_id: int,
    db=Depends(get_db),
):
    """
    Get all media assets for a project (Point 12: Rich Media API).
    
    Returns structured media objects instead of plain URL strings.
    Each asset includes:
    - Type classification (gallery, floorplan, masterplan, etc.)
    - Dimensions (width, height) when available
    - File metadata (size, format, MIME type)
    - License information
    - Optional unit type linking for floorplans
    
    ## Response Structure
    Media is organized by type:
    - **gallery**: Project images
    - **floorplans**: Unit layout drawings (linked to unit types when available)
    - **masterplans**: Site/building plans
    - **brochures**: PDF documents
    - **videos**: Video content
    
    ## Example Response
    ```json
    {
        "project_id": 123,
        "project_name": "ABC Residency",
        "gallery": [
            {
                "id": 1,
                "type": "gallery",
                "url": "https://...",
                "width_px": 1920,
                "height_px": 1080,
                "filesize_kb": 450,
                "file_format": "jpg",
                "license_type": "rera_official",
                "is_primary": true
            }
        ],
        "floorplans": [...],
        "masterplans": [...],
        "brochures": [...],
        "videos": [],
        "total_count": 15
    }
    ```
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Fetch artifacts
    artifacts = (
        db.query(ProjectArtifact)
        .filter(ProjectArtifact.project_id == project_id)
        .all()
    )
    
    # Fetch documents
    documents = (
        db.query(ProjectDocument)
        .filter(ProjectDocument.project_id == project_id)
        .all()
    )
    
    # Convert to media assets
    media_assets: list[MediaAsset] = []
    
    for i, artifact in enumerate(artifacts):
        media_assets.append(_artifact_to_media_asset(artifact, sort_order=i))
    
    for i, doc in enumerate(documents):
        media_assets.append(_document_to_media_asset(doc, sort_order=len(artifacts) + i))
    
    # Categorize by type
    gallery = [m for m in media_assets if m.type == MediaTypeEnum.GALLERY]
    floorplans = [m for m in media_assets if m.type == MediaTypeEnum.FLOORPLAN]
    masterplans = [m for m in media_assets if m.type == MediaTypeEnum.MASTERPLAN]
    brochures = [m for m in media_assets if m.type == MediaTypeEnum.BROCHURE]
    videos = [m for m in media_assets if m.type == MediaTypeEnum.VIDEO]
    
    # Sort each category (primary first, then by sort_order)
    for category in [gallery, floorplans, masterplans, brochures, videos]:
        category.sort(key=lambda m: (not m.is_primary, m.sort_order))
    
    return ProjectMediaResponse(
        project_id=project_id,
        project_name=project.project_name,
        gallery=gallery,
        floorplans=floorplans,
        masterplans=masterplans,
        brochures=brochures,
        videos=videos,
        total_count=len(media_assets),
    )


__all__ = ["router"]
