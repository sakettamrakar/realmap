"""
CG RERA Extractor - Complete extraction pipeline for RERA PDF documents.

This package provides:
- Configuration management for scraping
- OCR module for PDF text extraction
- LLM extraction for structured data
- Enrichment module for data merging
- Run processing orchestration
"""

from .config.loader import load_config
from .config.models import (
    AppConfig,
    BrowserConfig,
    RunConfig,
    RunMode,
    SearchFilterConfig,
    SearchPageConfig,
    SearchPageSelectorsConfig,
)

# OCR components
from .ocr import (
    PDFConverter,
    OCREngine,
    TextCleaner,
    OCRConfig,
)

# Extraction components
from .extraction import (
    DocumentClassifier,
    DocumentType,
    LLMExtractor,
)

# Enrichment components
from .enrichment import (
    DataMerger,
    ConflictResolver,
    MergeResult,
)

# Run processing
from .runs import (
    PDFProcessor,
    ProcessingResult,
    RunProcessingResult,
)

__version__ = "1.0.0"

__all__ = [
    # Version
    "__version__",
    # Config
    "AppConfig",
    "BrowserConfig",
    "RunMode",
    "RunConfig",
    "SearchFilterConfig",
    "SearchPageConfig",
    "SearchPageSelectorsConfig",
    "load_config",
    # OCR
    "PDFConverter",
    "OCREngine",
    "TextCleaner",
    "OCRConfig",
    # Extraction
    "DocumentClassifier",
    "DocumentType",
    "LLMExtractor",
    # Enrichment
    "DataMerger",
    "ConflictResolver",
    "MergeResult",
    # Run processing
    "PDFProcessor",
    "ProcessingResult",
    "RunProcessingResult",
]
