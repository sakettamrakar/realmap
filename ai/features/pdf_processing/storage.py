"""
Storage layer for PDF document extraction results.

Handles persisting extraction results to the database and
retrieving existing extractions.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from .base import ProcessingResult
from .db_models import DocumentDownload, DocumentExtraction, create_extraction_from_result

logger = logging.getLogger(__name__)


class ExtractionStorage:
    """
    Handles database operations for document extractions.
    
    Provides methods to:
    - Save extraction results
    - Query existing extractions
    - Track download status
    - Manage processing state
    
    Usage:
        from cg_rera_extractor.db.base import get_engine, get_session_local
        
        engine = get_engine()
        SessionLocal = get_session_local(engine)
        
        with SessionLocal() as session:
            storage = ExtractionStorage(session)
            storage.save_result(result, project_id=123)
    """
    
    def __init__(self, session: Session):
        """
        Initialize storage with database session.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
    
    # =========================================================================
    # EXTRACTION OPERATIONS
    # =========================================================================
    
    def save_result(
        self,
        result: ProcessingResult,
        project_id: int,
        document_id: Optional[int] = None,
        commit: bool = True
    ) -> DocumentExtraction:
        """
        Save a ProcessingResult to the database.
        
        Args:
            result: ProcessingResult from a PDF processor
            project_id: ID of the associated project
            document_id: Optional ID of the ProjectDocument
            commit: Whether to commit the transaction
            
        Returns:
            The created DocumentExtraction record
        """
        extraction = create_extraction_from_result(
            result=result,
            project_id=project_id,
            document_id=document_id
        )
        
        self.session.add(extraction)
        
        if commit:
            self.session.commit()
            self.session.refresh(extraction)
            logger.info(
                f"Saved extraction {extraction.id} for {result.filename} "
                f"(type: {result.document_type.value if result.document_type else 'unknown'})"
            )
        
        return extraction
    
    def save_batch(
        self,
        results: list[tuple[ProcessingResult, int, Optional[int]]],
        commit: bool = True
    ) -> list[DocumentExtraction]:
        """
        Save multiple extraction results in a batch.
        
        Args:
            results: List of tuples (ProcessingResult, project_id, document_id)
            commit: Whether to commit the transaction
            
        Returns:
            List of created DocumentExtraction records
        """
        extractions = []
        
        for result, project_id, document_id in results:
            extraction = create_extraction_from_result(
                result=result,
                project_id=project_id,
                document_id=document_id
            )
            self.session.add(extraction)
            extractions.append(extraction)
        
        if commit:
            self.session.commit()
            for extraction in extractions:
                self.session.refresh(extraction)
            logger.info(f"Saved batch of {len(extractions)} extractions")
        
        return extractions
    
    def get_extraction(self, extraction_id: int) -> Optional[DocumentExtraction]:
        """Get a single extraction by ID."""
        return self.session.get(DocumentExtraction, extraction_id)
    
    def get_extractions_for_project(
        self,
        project_id: int,
        document_type: Optional[str] = None
    ) -> Sequence[DocumentExtraction]:
        """
        Get all extractions for a project.
        
        Args:
            project_id: ID of the project
            document_type: Optional filter by document type
            
        Returns:
            List of DocumentExtraction records
        """
        stmt = select(DocumentExtraction).where(
            DocumentExtraction.project_id == project_id
        )
        
        if document_type:
            stmt = stmt.where(DocumentExtraction.document_type == document_type)
        
        stmt = stmt.order_by(DocumentExtraction.processed_at.desc())
        
        return self.session.execute(stmt).scalars().all()
    
    def get_extractions_by_document(
        self,
        document_id: int
    ) -> Sequence[DocumentExtraction]:
        """Get all extractions for a specific document."""
        stmt = select(DocumentExtraction).where(
            DocumentExtraction.document_id == document_id
        ).order_by(DocumentExtraction.processed_at.desc())
        
        return self.session.execute(stmt).scalars().all()
    
    def get_latest_extraction_for_file(
        self,
        file_path: str
    ) -> Optional[DocumentExtraction]:
        """Get the most recent extraction for a file path."""
        stmt = select(DocumentExtraction).where(
            DocumentExtraction.file_path == file_path
        ).order_by(DocumentExtraction.processed_at.desc()).limit(1)
        
        return self.session.execute(stmt).scalars().first()
    
    def file_already_processed(
        self,
        file_path: str,
        processor_name: Optional[str] = None
    ) -> bool:
        """
        Check if a file has already been processed.
        
        Args:
            file_path: Path to the PDF file
            processor_name: Optional - check for specific processor
            
        Returns:
            True if file has been successfully processed
        """
        stmt = select(DocumentExtraction.id).where(
            DocumentExtraction.file_path == file_path,
            DocumentExtraction.success == True
        )
        
        if processor_name:
            stmt = stmt.where(DocumentExtraction.processor_name == processor_name)
        
        stmt = stmt.limit(1)
        
        return self.session.execute(stmt).scalars().first() is not None
    
    def delete_extraction(self, extraction_id: int, commit: bool = True) -> bool:
        """Delete an extraction by ID."""
        extraction = self.session.get(DocumentExtraction, extraction_id)
        if extraction:
            self.session.delete(extraction)
            if commit:
                self.session.commit()
            return True
        return False
    
    # =========================================================================
    # DOWNLOAD TRACKING OPERATIONS
    # =========================================================================
    
    def create_download(
        self,
        project_id: int,
        source_url: str,
        document_name: Optional[str] = None,
        document_id: Optional[int] = None,
        commit: bool = True
    ) -> DocumentDownload:
        """
        Create a new download tracking record.
        
        Args:
            project_id: ID of the associated project
            source_url: URL to download from
            document_name: Optional document name
            document_id: Optional ProjectDocument ID
            commit: Whether to commit
            
        Returns:
            The created DocumentDownload record
        """
        download = DocumentDownload(
            project_id=project_id,
            source_url=source_url,
            document_name=document_name,
            document_id=document_id,
            download_status="pending"
        )
        
        self.session.add(download)
        
        if commit:
            self.session.commit()
            self.session.refresh(download)
        
        return download
    
    def update_download_status(
        self,
        download_id: int,
        status: str,
        local_path: Optional[str] = None,
        filename: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        error: Optional[str] = None,
        commit: bool = True
    ) -> Optional[DocumentDownload]:
        """
        Update download status.
        
        Args:
            download_id: ID of the download record
            status: New status (pending, downloading, completed, failed)
            local_path: Path to downloaded file
            filename: Downloaded filename
            file_size_bytes: Size of downloaded file
            error: Error message if failed
            commit: Whether to commit
            
        Returns:
            Updated DocumentDownload or None if not found
        """
        download = self.session.get(DocumentDownload, download_id)
        if not download:
            return None
        
        download.download_status = status
        
        if local_path:
            download.local_path = local_path
        if filename:
            download.filename = filename
        if file_size_bytes:
            download.file_size_bytes = file_size_bytes
        if error:
            download.download_error = error
            download.retry_count += 1
        
        if status == "completed":
            from datetime import datetime, timezone
            download.downloaded_at = datetime.now(timezone.utc)
        
        if commit:
            self.session.commit()
            self.session.refresh(download)
        
        return download
    
    def get_pending_downloads(
        self,
        project_id: Optional[int] = None,
        limit: int = 100
    ) -> Sequence[DocumentDownload]:
        """Get downloads that need to be processed."""
        stmt = select(DocumentDownload).where(
            DocumentDownload.download_status.in_(["pending", "failed"])
        )
        
        if project_id:
            stmt = stmt.where(DocumentDownload.project_id == project_id)
        
        stmt = stmt.order_by(
            DocumentDownload.retry_count.asc(),
            DocumentDownload.created_at.asc()
        ).limit(limit)
        
        return self.session.execute(stmt).scalars().all()
    
    def get_completed_downloads(
        self,
        project_id: int,
        unprocessed_only: bool = False
    ) -> Sequence[DocumentDownload]:
        """
        Get completed downloads for a project.
        
        Args:
            project_id: ID of the project
            unprocessed_only: If True, only return downloads without extractions
            
        Returns:
            List of DocumentDownload records
        """
        stmt = select(DocumentDownload).where(
            DocumentDownload.project_id == project_id,
            DocumentDownload.download_status == "completed"
        )
        
        downloads = self.session.execute(stmt).scalars().all()
        
        if unprocessed_only:
            # Filter out downloads that have already been processed
            result = []
            for download in downloads:
                if download.local_path and not self.file_already_processed(download.local_path):
                    result.append(download)
            return result
        
        return downloads
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_extraction_stats(
        self,
        project_id: Optional[int] = None
    ) -> dict:
        """
        Get extraction statistics.
        
        Args:
            project_id: Optional filter by project
            
        Returns:
            Dictionary with statistics
        """
        from sqlalchemy import func
        
        base_query = select(DocumentExtraction)
        if project_id:
            base_query = base_query.where(DocumentExtraction.project_id == project_id)
        
        # Total extractions
        total = self.session.execute(
            select(func.count()).select_from(
                base_query.subquery()
            )
        ).scalar() or 0
        
        # Successful extractions
        successful = self.session.execute(
            select(func.count()).select_from(
                base_query.where(DocumentExtraction.success == True).subquery()
            )
        ).scalar() or 0
        
        # By document type
        type_counts = self.session.execute(
            select(
                DocumentExtraction.document_type,
                func.count().label("count")
            ).where(
                DocumentExtraction.project_id == project_id if project_id else True
            ).group_by(DocumentExtraction.document_type)
        ).all()
        
        # By processor
        processor_counts = self.session.execute(
            select(
                DocumentExtraction.processor_name,
                func.count().label("count")
            ).where(
                DocumentExtraction.project_id == project_id if project_id else True
            ).group_by(DocumentExtraction.processor_name)
        ).all()
        
        return {
            "total_extractions": total,
            "successful": successful,
            "failed": total - successful,
            "by_document_type": {t: c for t, c in type_counts if t},
            "by_processor": {p: c for p, c in processor_counts},
        }
