"""
Extraction Module for Document Processing

This module provides document classification and LLM-based
structured data extraction from OCR text.

Components:
- DocumentClassifier: Identify document type from content
- LLMExtractor: Extract structured data using LLM
- Schemas: Pydantic models for each document type

Usage:
    from cg_rera_extractor.extraction import DocumentClassifier, LLMExtractor
    
    # Classify document
    classifier = DocumentClassifier()
    doc_type = classifier.classify(ocr_text, filename)
    
    # Extract structured data
    extractor = LLMExtractor()
    data = extractor.extract(ocr_text, doc_type)
"""

from .document_classifier import DocumentClassifier, DocumentType
from .llm_extractor import LLMExtractor

__all__ = [
    "DocumentClassifier",
    "DocumentType",
    "LLMExtractor"
]
