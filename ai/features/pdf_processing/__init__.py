"""
PDF Processing Feature Module.

This module provides a complete pipeline for:
1. Processing PDFs with multiple extractors (text-only, LLM-based)
2. Extracting structured metadata (dates, amounts, areas, reference numbers)
3. Classifying document types (Building Permission, NOC, Registration, etc.)
4. Storing extraction results in database

Architecture:
- BasePDFProcessor: Abstract base class with common functionality
- TextExtractor: Fast local processing with pypdf + regex
- LLMExtractor: AI-powered semantic extraction
- PDFOrchestrator: Coordinates processing mode selection and batch processing
- ExtractionStorage: Database persistence layer

Usage:
    from ai.features.pdf_processing import (
        PDFOrchestrator,
        ProcessingMode,
        TextExtractor,
        LLMExtractor,
    )
    
    # Simple text extraction
    extractor = TextExtractor()
    result = extractor.process(Path("document.pdf"))
    print(f"Type: {result.document_type}, Pages: {result.page_count}")
    
    # Batch processing with orchestrator
    orchestrator = PDFOrchestrator()
    batch = orchestrator.process_directory(
        Path("pdfs/"),
        mode=ProcessingMode.HYBRID
    )
    print(f"Processed {batch.successful}/{batch.total_files}")
    
    # With database storage
    from cg_rera_extractor.db.base import get_engine, get_session_local
    engine = get_engine()
    with get_session_local(engine)() as session:
        orchestrator = PDFOrchestrator(db_session=session)
        orchestrator.process_directory_and_store(
            Path("pdfs/"),
            project_id=123,
            mode=ProcessingMode.TEXT_ONLY
        )
"""

# Base classes and types
from .base import (
    BasePDFProcessor,
    ProcessingResult,
    ExtractedMetadata,
    DocumentType,
)

# Processors
from .text_extractor import TextExtractor
from .llm_extractor import LLMExtractor

# Orchestration
from .orchestrator import (
    PDFOrchestrator,
    ProcessingMode,
    BatchResult,
)

# Storage
from .storage import ExtractionStorage

# Database models
from .db_models import (
    DocumentExtraction,
    DocumentDownload,
    create_extraction_from_result,
)

__all__ = [
    # Base
    "BasePDFProcessor",
    "ProcessingResult",
    "ExtractedMetadata",
    "DocumentType",
    # Processors
    "TextExtractor",
    "LLMExtractor",
    # Orchestration
    "PDFOrchestrator",
    "ProcessingMode",
    "BatchResult",
    # Storage
    "ExtractionStorage",
    # DB Models
    "DocumentExtraction",
    "DocumentDownload",
    "create_extraction_from_result",
]
