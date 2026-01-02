"""
Run processing module for CG RERA Extractor.

This module provides orchestration for processing PDF documents
from scraped run directories.
"""

from .pdf_processor import (
    PDFProcessor,
    ProcessingResult,
    RunProcessingResult,
    process_multiple_runs,
)

__all__ = [
    "PDFProcessor",
    "ProcessingResult",
    "RunProcessingResult",
    "process_multiple_runs",
]
