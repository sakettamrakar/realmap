"""
Database models for PDF document extraction.

This module extends the existing database schema to store PDF processing results.
Uses the existing ReraFiling model pattern but adds more structured extraction data.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

# Import Base from existing models
from cg_rera_extractor.db.base import Base


class DocumentExtraction(Base):
    """
    Stores extracted data from PDF documents.
    
    Extends the pattern from ReraFiling to provide more structured
    extraction results with support for multiple processing methods.
    
    Relationships:
    - Links to ProjectDocument via document_id
    - Links to Project via project_id
    """
    
    __tablename__ = "document_extractions"
    __table_args__ = (
        Index("ix_document_extractions_project_id", "project_id"),
        Index("ix_document_extractions_document_id", "document_id"),
        Index("ix_document_extractions_document_type", "document_type"),
        Index("ix_document_extractions_processor_name", "processor_name"),
    )
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_documents.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # File Information
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    page_count: Mapped[int | None] = mapped_column(Integer)
    
    # Document Classification
    document_type: Mapped[str | None] = mapped_column(
        String(50),
        doc="Classified document type (BUILDING_PERMISSION, NOC, etc.)"
    )
    document_type_confidence: Mapped[float | None] = mapped_column(
        Float,
        doc="Confidence score for document type classification (0.0-1.0)"
    )
    
    # Extracted Text
    raw_text: Mapped[str | None] = mapped_column(
        Text,
        doc="Full extracted text from PDF"
    )
    text_length: Mapped[int | None] = mapped_column(Integer)
    
    # Structured Extracted Data (JSON)
    extracted_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        doc="Structured metadata: dates, amounts, areas, reference numbers"
    )
    
    # Key Extracted Fields (denormalized for easy querying)
    approval_number: Mapped[str | None] = mapped_column(String(100))
    approval_date: Mapped[str | None] = mapped_column(String(50))
    validity_date: Mapped[str | None] = mapped_column(String(50))
    issuing_authority: Mapped[str | None] = mapped_column(String(255))
    total_area_sqft: Mapped[float | None] = mapped_column(Float)
    total_cost: Mapped[float | None] = mapped_column(Float)
    floor_count: Mapped[int | None] = mapped_column(Integer)
    unit_count: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[str | None] = mapped_column(
        String(1000),
        doc="AI-generated summary of the document"
    )
    
    # Processing Metadata
    processor_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Name of processor used (text_extractor, llm_extractor)"
    )
    processor_version: Mapped[str | None] = mapped_column(String(20))
    processing_time_ms: Mapped[int | None] = mapped_column(Integer)
    
    # Status
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(String(500))
    warnings: Mapped[list[str] | None] = mapped_column(JSON)
    
    # Timestamps
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    # Note: Relationships are defined here but require the models to exist
    # project: Mapped["Project"] = relationship(back_populates="document_extractions")
    # document: Mapped["ProjectDocument"] = relationship(back_populates="extractions")
    
    def __repr__(self) -> str:
        return (
            f"<DocumentExtraction(id={self.id}, "
            f"filename='{self.filename}', "
            f"type='{self.document_type}')>"
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "document_id": self.document_id,
            "file_path": self.file_path,
            "filename": self.filename,
            "file_size_bytes": self.file_size_bytes,
            "page_count": self.page_count,
            "document_type": self.document_type,
            "document_type_confidence": self.document_type_confidence,
            "text_length": self.text_length,
            "extracted_metadata": self.extracted_metadata,
            "approval_number": self.approval_number,
            "approval_date": self.approval_date,
            "validity_date": self.validity_date,
            "issuing_authority": self.issuing_authority,
            "total_area_sqft": self.total_area_sqft,
            "total_cost": self.total_cost,
            "floor_count": self.floor_count,
            "unit_count": self.unit_count,
            "summary": self.summary,
            "processor_name": self.processor_name,
            "processor_version": self.processor_version,
            "processing_time_ms": self.processing_time_ms,
            "success": self.success,
            "error": self.error,
            "warnings": self.warnings,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }


class DocumentDownload(Base):
    """
    Tracks downloaded PDF documents.
    
    Stores information about downloaded PDFs before they are processed.
    Links the remote URL to the local file path.
    """
    
    __tablename__ = "document_downloads"
    __table_args__ = (
        Index("ix_document_downloads_project_id", "project_id"),
        Index("ix_document_downloads_download_status", "download_status"),
    )
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_documents.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Source Information
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    document_name: Mapped[str | None] = mapped_column(
        String(255),
        doc="Original document name from source"
    )
    
    # Local File Information
    local_path: Mapped[str | None] = mapped_column(
        String(1024),
        doc="Local file path after download"
    )
    filename: Mapped[str | None] = mapped_column(String(255))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    content_type: Mapped[str | None] = mapped_column(String(100))
    
    # Download Status
    download_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        doc="Status: pending, downloading, completed, failed"
    )
    download_error: Mapped[str | None] = mapped_column(String(500))
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    def __repr__(self) -> str:
        return (
            f"<DocumentDownload(id={self.id}, "
            f"url='{self.source_url[:50]}...', "
            f"status='{self.download_status}')>"
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_extraction_from_result(
    result: "ProcessingResult",
    project_id: int,
    document_id: Optional[int] = None
) -> DocumentExtraction:
    """
    Create a DocumentExtraction instance from a ProcessingResult.
    
    Args:
        result: ProcessingResult from a PDF processor
        project_id: ID of the associated project
        document_id: Optional ID of the associated ProjectDocument
        
    Returns:
        DocumentExtraction instance (not yet committed to DB)
    """
    # Convert metadata to dict
    metadata_dict = None
    if result.metadata:
        metadata_dict = {
            "dates": result.metadata.dates,
            "amounts": result.metadata.amounts,
            "areas": result.metadata.areas,
            "reference_numbers": result.metadata.reference_numbers,
        }
    
    extraction = DocumentExtraction(
        project_id=project_id,
        document_id=document_id,
        file_path=result.file_path,
        filename=result.filename,
        file_size_bytes=result.file_size_bytes,
        page_count=result.page_count,
        document_type=result.document_type.value if result.document_type else None,
        document_type_confidence=result.document_type_confidence,
        raw_text=result.extracted_text,
        text_length=result.text_length,
        extracted_metadata=metadata_dict,
        approval_number=result.metadata.approval_number if result.metadata else None,
        approval_date=result.metadata.approval_date if result.metadata else None,
        validity_date=result.metadata.validity_date if result.metadata else None,
        issuing_authority=result.metadata.issuing_authority if result.metadata else None,
        total_area_sqft=result.metadata.total_area_sqft if result.metadata else None,
        total_cost=result.metadata.total_cost if result.metadata else None,
        floor_count=result.metadata.floor_count if result.metadata else None,
        unit_count=result.metadata.unit_count if result.metadata else None,
        summary=result.metadata.summary if result.metadata else None,
        processor_name=result.processor_name,
        processor_version=result.processor_version,
        processing_time_ms=result.processing_time_ms,
        success=result.success,
        error=result.error,
        warnings=result.warnings if result.warnings else None,
    )
    
    return extraction
