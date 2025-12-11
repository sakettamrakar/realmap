"""
PDF Processing Orchestrator.

Coordinates the complete PDF processing pipeline:
1. Discovers PDF files to process
2. Selects appropriate processor (text or LLM)
3. Processes PDFs and extracts data
4. Stores results in database

Usage:
    from ai.features.pdf_processing import PDFOrchestrator, ProcessingMode
    
    # Process a single file
    orchestrator = PDFOrchestrator()
    result = orchestrator.process_file(Path("document.pdf"))
    
    # Process a directory
    results = orchestrator.process_directory(Path("pdfs/"), project_id=123)
    
    # Process with database storage
    orchestrator = PDFOrchestrator(db_session=session)
    results = orchestrator.process_and_store(
        Path("pdfs/"),
        project_id=123,
        mode=ProcessingMode.HYBRID
    )
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Sequence

from sqlalchemy.orm import Session

from .base import DocumentType, ProcessingResult
from .text_extractor import TextExtractor
from .llm_extractor import LLMExtractor
from .storage import ExtractionStorage

logger = logging.getLogger(__name__)


class ProcessingMode(str, Enum):
    """Processing mode selection."""
    TEXT_ONLY = "text_only"       # Fast, local, no AI
    LLM_ONLY = "llm_only"         # AI-powered extraction
    HYBRID = "hybrid"             # Text first, LLM for complex docs
    AUTO = "auto"                 # Automatically select based on document


@dataclass
class BatchResult:
    """Results from batch processing."""
    total_files: int = 0
    processed: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    results: list[ProcessingResult] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)
    processing_time_ms: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.processed == 0:
            return 0.0
        return self.successful / self.processed
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_files": self.total_files,
            "processed": self.processed,
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": round(self.success_rate * 100, 1),
            "processing_time_ms": self.processing_time_ms,
            "errors": [{"file": f, "error": e} for f, e in self.errors],
        }


class PDFOrchestrator:
    """
    Main orchestrator for PDF processing pipeline.
    
    Coordinates between:
    - File discovery
    - Processor selection (text vs LLM)
    - Extraction execution
    - Database storage
    
    Supports multiple processing modes:
    - TEXT_ONLY: Fast local processing with regex
    - LLM_ONLY: AI-powered semantic extraction
    - HYBRID: Text first, LLM for uncertain classifications
    - AUTO: Automatic selection based on document characteristics
    """
    
    def __init__(
        self,
        db_session: Optional[Session] = None,
        text_max_pages: int = 20,
        llm_max_pages: int = 10,
        llm_max_tokens: int = 512,
        skip_processed: bool = True
    ):
        """
        Initialize orchestrator.
        
        Args:
            db_session: Optional database session for storage
            text_max_pages: Max pages for text extraction
            llm_max_pages: Max pages for LLM extraction
            llm_max_tokens: Max tokens for LLM responses
            skip_processed: Skip files already in database
        """
        self.db_session = db_session
        self.text_max_pages = text_max_pages
        self.llm_max_pages = llm_max_pages
        self.llm_max_tokens = llm_max_tokens
        self.skip_processed = skip_processed
        
        # Lazy-load processors
        self._text_processor: Optional[TextExtractor] = None
        self._llm_processor: Optional[LLMExtractor] = None
        self._storage: Optional[ExtractionStorage] = None
    
    @property
    def text_processor(self) -> TextExtractor:
        """Get or create text processor."""
        if self._text_processor is None:
            self._text_processor = TextExtractor(max_pages=self.text_max_pages)
        return self._text_processor
    
    @property
    def llm_processor(self) -> LLMExtractor:
        """Get or create LLM processor."""
        if self._llm_processor is None:
            self._llm_processor = LLMExtractor(
                max_pages=self.llm_max_pages,
                max_tokens=self.llm_max_tokens,
                fallback_to_text=True
            )
        return self._llm_processor
    
    @property
    def storage(self) -> Optional[ExtractionStorage]:
        """Get storage layer if session available."""
        if self._storage is None and self.db_session is not None:
            self._storage = ExtractionStorage(self.db_session)
        return self._storage
    
    # =========================================================================
    # SINGLE FILE PROCESSING
    # =========================================================================
    
    def process_file(
        self,
        pdf_path: Path,
        mode: ProcessingMode = ProcessingMode.TEXT_ONLY
    ) -> ProcessingResult:
        """
        Process a single PDF file.
        
        Args:
            pdf_path: Path to PDF file
            mode: Processing mode to use
            
        Returns:
            ProcessingResult with extracted data
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            return ProcessingResult(
                file_path=str(pdf_path),
                filename=pdf_path.name,
                file_size_bytes=0,
                page_count=0,
                document_type=DocumentType.UNKNOWN,
                document_type_confidence=0.0,
                extracted_text="",
                text_length=0,
                metadata=None,
                processor_name="orchestrator",
                processor_version="1.0",
                success=False,
                error=f"File not found: {pdf_path}"
            )
        
        if mode == ProcessingMode.TEXT_ONLY:
            return self.text_processor.process(pdf_path)
        
        elif mode == ProcessingMode.LLM_ONLY:
            return self.llm_processor.process(pdf_path)
        
        elif mode == ProcessingMode.HYBRID:
            return self._process_hybrid(pdf_path)
        
        elif mode == ProcessingMode.AUTO:
            return self._process_auto(pdf_path)
        
        else:
            # Default to text
            return self.text_processor.process(pdf_path)
    
    def _process_hybrid(self, pdf_path: Path) -> ProcessingResult:
        """
        Hybrid processing: text first, LLM for low confidence.
        
        Strategy:
        1. Try text extraction first (fast)
        2. If confidence < 0.5 or type is UNKNOWN, use LLM
        3. Merge results if both run
        """
        # First pass: text extraction
        text_result = self.text_processor.process(pdf_path)
        
        # Check if we need LLM
        needs_llm = (
            not text_result.success or
            text_result.document_type == DocumentType.UNKNOWN or
            (text_result.document_type_confidence or 0) < 0.5 or
            text_result.text_length < 100
        )
        
        if not needs_llm:
            return text_result
        
        # Second pass: LLM extraction
        logger.info(f"Low confidence ({text_result.document_type_confidence:.2f}), using LLM")
        llm_result = self.llm_processor.process(pdf_path)
        
        # Prefer LLM result if successful
        if llm_result.success:
            return llm_result
        
        # Fall back to text result
        return text_result
    
    def _process_auto(self, pdf_path: Path) -> ProcessingResult:
        """
        Auto-select processor based on file characteristics.
        
        Strategy:
        - Small files (< 100KB): Text only
        - Large files or scanned: LLM
        - Known document types: Text
        - Unknown: Hybrid
        """
        file_size = pdf_path.stat().st_size
        filename_lower = pdf_path.name.lower()
        
        # Small files: text is usually sufficient
        if file_size < 100_000:  # 100KB
            return self.text_processor.process(pdf_path)
        
        # Check filename for known patterns
        text_patterns = [
            "registration", "certificate", "agreement",
            "approval", "permission", "noc", "sanction"
        ]
        
        is_known_type = any(p in filename_lower for p in text_patterns)
        
        if is_known_type:
            # Try text first for known types
            text_result = self.text_processor.process(pdf_path)
            if text_result.success and text_result.text_length > 200:
                return text_result
        
        # Default to hybrid for unknown or complex documents
        return self._process_hybrid(pdf_path)
    
    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================
    
    def discover_pdfs(self, directory: Path, recursive: bool = True) -> list[Path]:
        """
        Discover PDF files in a directory.
        
        Args:
            directory: Directory to search
            recursive: Search subdirectories
            
        Returns:
            List of PDF file paths
        """
        directory = Path(directory)
        
        if not directory.exists():
            logger.warning(f"Directory not found: {directory}")
            return []
        
        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdfs = list(directory.glob(pattern))
        
        # Sort by name for consistent ordering
        pdfs.sort(key=lambda p: p.name.lower())
        
        logger.info(f"Discovered {len(pdfs)} PDF files in {directory}")
        return pdfs
    
    def process_directory(
        self,
        directory: Path,
        mode: ProcessingMode = ProcessingMode.TEXT_ONLY,
        recursive: bool = True,
        max_files: Optional[int] = None
    ) -> BatchResult:
        """
        Process all PDFs in a directory.
        
        Args:
            directory: Directory containing PDFs
            mode: Processing mode
            recursive: Search subdirectories
            max_files: Maximum files to process
            
        Returns:
            BatchResult with all processing results
        """
        import time
        start_time = time.time()
        
        # Discover PDFs
        pdf_files = self.discover_pdfs(directory, recursive)
        
        if max_files:
            pdf_files = pdf_files[:max_files]
        
        batch_result = BatchResult(total_files=len(pdf_files))
        
        for pdf_path in pdf_files:
            try:
                result = self.process_file(pdf_path, mode)
                batch_result.results.append(result)
                batch_result.processed += 1
                
                if result.success:
                    batch_result.successful += 1
                else:
                    batch_result.failed += 1
                    batch_result.errors.append((str(pdf_path), result.error or "Unknown error"))
                
            except Exception as e:
                logger.error(f"Error processing {pdf_path}: {e}")
                batch_result.failed += 1
                batch_result.errors.append((str(pdf_path), str(e)))
        
        batch_result.processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"Batch complete: {batch_result.successful}/{batch_result.processed} successful "
            f"({batch_result.success_rate*100:.1f}%) in {batch_result.processing_time_ms}ms"
        )
        
        return batch_result
    
    # =========================================================================
    # PROCESSING WITH DATABASE STORAGE
    # =========================================================================
    
    def process_and_store(
        self,
        pdf_path: Path,
        project_id: int,
        document_id: Optional[int] = None,
        mode: ProcessingMode = ProcessingMode.TEXT_ONLY
    ) -> ProcessingResult:
        """
        Process a PDF and store results in database.
        
        Args:
            pdf_path: Path to PDF file
            project_id: Associated project ID
            document_id: Optional ProjectDocument ID
            mode: Processing mode
            
        Returns:
            ProcessingResult (also stored in DB)
        """
        pdf_path = Path(pdf_path)
        
        # Check if already processed
        if self.skip_processed and self.storage:
            if self.storage.file_already_processed(str(pdf_path)):
                logger.info(f"Skipping already processed: {pdf_path.name}")
                result = ProcessingResult(
                    file_path=str(pdf_path),
                    filename=pdf_path.name,
                    file_size_bytes=0,
                    page_count=0,
                    document_type=DocumentType.UNKNOWN,
                    document_type_confidence=0.0,
                    extracted_text="",
                    text_length=0,
                    metadata=None,
                    processor_name="orchestrator",
                    processor_version="1.0",
                    success=True,
                    warnings=["Skipped - already processed"]
                )
                return result
        
        # Process the file
        result = self.process_file(pdf_path, mode)
        
        # Store in database
        if self.storage and result.success:
            try:
                self.storage.save_result(
                    result=result,
                    project_id=project_id,
                    document_id=document_id
                )
            except Exception as e:
                logger.error(f"Failed to store result for {pdf_path}: {e}")
                result.warnings.append(f"Storage failed: {e}")
        
        return result
    
    def process_directory_and_store(
        self,
        directory: Path,
        project_id: int,
        mode: ProcessingMode = ProcessingMode.TEXT_ONLY,
        recursive: bool = True,
        max_files: Optional[int] = None
    ) -> BatchResult:
        """
        Process all PDFs in directory and store in database.
        
        Args:
            directory: Directory containing PDFs
            project_id: Associated project ID
            mode: Processing mode
            recursive: Search subdirectories
            max_files: Maximum files to process
            
        Returns:
            BatchResult with all processing results
        """
        import time
        start_time = time.time()
        
        pdf_files = self.discover_pdfs(directory, recursive)
        
        if max_files:
            pdf_files = pdf_files[:max_files]
        
        batch_result = BatchResult(total_files=len(pdf_files))
        
        for pdf_path in pdf_files:
            try:
                # Check if should skip
                if self.skip_processed and self.storage:
                    if self.storage.file_already_processed(str(pdf_path)):
                        batch_result.skipped += 1
                        continue
                
                result = self.process_file(pdf_path, mode)
                batch_result.results.append(result)
                batch_result.processed += 1
                
                if result.success:
                    batch_result.successful += 1
                    
                    # Store in database
                    if self.storage:
                        try:
                            self.storage.save_result(
                                result=result,
                                project_id=project_id
                            )
                        except Exception as e:
                            logger.error(f"Storage failed for {pdf_path}: {e}")
                else:
                    batch_result.failed += 1
                    batch_result.errors.append((str(pdf_path), result.error or "Unknown"))
                
            except Exception as e:
                logger.error(f"Error processing {pdf_path}: {e}")
                batch_result.failed += 1
                batch_result.errors.append((str(pdf_path), str(e)))
        
        batch_result.processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"Batch complete: {batch_result.successful}/{batch_result.processed} stored "
            f"({batch_result.skipped} skipped) in {batch_result.processing_time_ms}ms"
        )
        
        return batch_result
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def generate_report(
        self,
        batch_result: BatchResult,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate a human-readable report from batch results.
        
        Args:
            batch_result: Results from batch processing
            output_path: Optional path to save report
            
        Returns:
            Report as string
        """
        lines = [
            "=" * 60,
            "PDF PROCESSING REPORT",
            f"Generated: {datetime.now().isoformat()}",
            "=" * 60,
            "",
            "SUMMARY",
            "-" * 40,
            f"Total Files:     {batch_result.total_files}",
            f"Processed:       {batch_result.processed}",
            f"Successful:      {batch_result.successful}",
            f"Failed:          {batch_result.failed}",
            f"Skipped:         {batch_result.skipped}",
            f"Success Rate:    {batch_result.success_rate*100:.1f}%",
            f"Processing Time: {batch_result.processing_time_ms}ms",
            "",
        ]
        
        # Document type breakdown
        type_counts: dict[str, int] = {}
        for result in batch_result.results:
            if result.success and result.document_type:
                doc_type = result.document_type.value
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        if type_counts:
            lines.extend([
                "DOCUMENT TYPES",
                "-" * 40,
            ])
            for doc_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
                lines.append(f"  {doc_type}: {count}")
            lines.append("")
        
        # Errors
        if batch_result.errors:
            lines.extend([
                "ERRORS",
                "-" * 40,
            ])
            for file_path, error in batch_result.errors[:10]:  # Limit to 10
                lines.append(f"  {Path(file_path).name}: {error[:50]}")
            if len(batch_result.errors) > 10:
                lines.append(f"  ... and {len(batch_result.errors) - 10} more")
            lines.append("")
        
        lines.append("=" * 60)
        
        report = "\n".join(lines)
        
        if output_path:
            output_path.write_text(report)
            logger.info(f"Report saved to {output_path}")
        
        return report
    
    def export_results_json(
        self,
        batch_result: BatchResult,
        output_path: Path
    ) -> None:
        """
        Export batch results to JSON.
        
        Args:
            batch_result: Results from batch processing
            output_path: Path to save JSON
        """
        data = {
            "summary": batch_result.to_dict(),
            "results": [
                {
                    "file": result.filename,
                    "success": result.success,
                    "document_type": result.document_type.value if result.document_type else None,
                    "confidence": result.document_type_confidence,
                    "page_count": result.page_count,
                    "text_length": result.text_length,
                    "processing_time_ms": result.processing_time_ms,
                    "metadata": {
                        "approval_number": result.metadata.approval_number if result.metadata else None,
                        "approval_date": result.metadata.approval_date if result.metadata else None,
                        "issuing_authority": result.metadata.issuing_authority if result.metadata else None,
                        "summary": result.metadata.summary if result.metadata else None,
                    } if result.metadata else None,
                    "error": result.error,
                }
                for result in batch_result.results
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results exported to {output_path}")
