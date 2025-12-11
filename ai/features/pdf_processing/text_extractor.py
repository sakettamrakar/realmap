"""
Text-based PDF Extractor.

Uses pypdf for text extraction with regex-based metadata extraction.
This is the fast, local processor that doesn't require AI/LLM.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False
    PdfReader = None

from .base import (
    BasePDFProcessor,
    DocumentType,
    ExtractedMetadata,
    ProcessingResult,
)

logger = logging.getLogger(__name__)


class TextExtractor(BasePDFProcessor):
    """
    Text-based PDF processor using pypdf.
    
    Features:
    - Fast local processing (no API calls)
    - Regex-based metadata extraction
    - Document type classification
    - Works offline
    
    Limitations:
    - Cannot process scanned PDFs (no OCR)
    - Limited semantic understanding
    - May miss context-dependent information
    
    Usage:
        extractor = TextExtractor()
        result = extractor.process(Path("document.pdf"))
        print(f"Type: {result.document_type}")
        print(f"Dates found: {result.metadata.dates}")
    """
    
    name = "text_extractor"
    version = "1.0"
    
    def __init__(self, max_pages: int = 20):
        """
        Initialize text extractor.
        
        Args:
            max_pages: Maximum pages to process (default: 20)
        """
        super().__init__()
        self.max_pages = max_pages
        
        if not HAS_PYPDF:
            raise ImportError(
                "pypdf is required for TextExtractor. "
                "Install with: pip install pypdf"
            )
    
    def process(self, pdf_path: Path) -> ProcessingResult:
        """
        Process a PDF file and extract text + metadata.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ProcessingResult with extracted data
        """
        start_time = time.time()
        
        # Initialize result with defaults
        result = ProcessingResult(
            file_path=str(pdf_path),
            filename=pdf_path.name,
            file_size_bytes=0,
            page_count=0,
            document_type=DocumentType.UNKNOWN,
            document_type_confidence=0.0,
            extracted_text="",
            text_length=0,
            metadata=ExtractedMetadata(),
            processor_name=self.name,
            processor_version=self.version,
        )
        
        # Validate PDF
        is_valid, error = self.validate_pdf(pdf_path)
        if not is_valid:
            result.success = False
            result.error = error
            return result
        
        result.file_size_bytes = pdf_path.stat().st_size
        
        try:
            # Extract text
            text_parts = []
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                result.page_count = len(reader.pages)
                
                # Process up to max_pages
                pages_to_process = min(len(reader.pages), self.max_pages)
                
                for i in range(pages_to_process):
                    try:
                        page_text = reader.pages[i].extract_text()
                        if page_text:
                            text_parts.append(f"--- Page {i+1} ---\n{page_text}")
                    except Exception as e:
                        result.warnings.append(f"Failed to extract page {i+1}: {e}")
                
                # Check if we truncated
                if len(reader.pages) > self.max_pages:
                    result.warnings.append(
                        f"Truncated: processed {self.max_pages} of {len(reader.pages)} pages"
                    )
            
            result.extracted_text = "\n\n".join(text_parts)
            result.text_length = len(result.extracted_text)
            
            # Check if we got meaningful text
            if result.text_length < 50:
                result.warnings.append(
                    "Very little text extracted - PDF may be scanned/image-based"
                )
            
            # Detect document type
            doc_type, confidence = self.detect_document_type(
                result.extracted_text,
                pdf_path.name
            )
            result.document_type = doc_type
            result.document_type_confidence = confidence
            
            # Extract metadata
            result.metadata = self._extract_metadata(result.extracted_text)
            
            result.success = True
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            logger.error(f"Failed to process {pdf_path}: {e}")
        
        # Record processing time
        result.processing_time_ms = int((time.time() - start_time) * 1000)
        
        return result
    
    def _extract_metadata(self, text: str) -> ExtractedMetadata:
        """Extract structured metadata from text."""
        metadata = ExtractedMetadata()
        
        # Extract dates
        metadata.dates = self.extract_dates(text)
        
        # Try to identify specific date types
        if metadata.dates:
            # Look for approval date
            for date in metadata.dates:
                # Check context around each date
                date_idx = text.lower().find(date.lower())
                if date_idx > 0:
                    context = text[max(0, date_idx-50):date_idx].lower()
                    if any(word in context for word in ['approval', 'sanctioned', 'granted', 'issued']):
                        metadata.approval_date = date
                        break
            
            # Look for validity/expiry date
            for date in metadata.dates:
                date_idx = text.lower().find(date.lower())
                if date_idx > 0:
                    context = text[max(0, date_idx-50):date_idx].lower()
                    if any(word in context for word in ['valid', 'expir', 'till', 'until']):
                        metadata.validity_date = date
                        break
        
        # Extract amounts
        metadata.amounts = self.extract_amounts(text)
        
        # Find total cost if mentioned
        if metadata.amounts:
            for amt in metadata.amounts:
                # Check if this is a total
                amt_text = amt.get('raw', '')
                amt_idx = text.lower().find(amt_text.lower())
                if amt_idx > 0:
                    context = text[max(0, amt_idx-100):amt_idx].lower()
                    if any(word in context for word in ['total', 'project cost', 'estimated cost']):
                        metadata.total_cost = amt['amount']
                        break
        
        # Extract areas
        metadata.areas = self.extract_areas(text)
        
        # Find total area if mentioned
        if metadata.areas:
            for area in metadata.areas:
                area_text = area.get('raw', '')
                area_idx = text.lower().find(area_text.lower())
                if area_idx > 0:
                    context = text[max(0, area_idx-100):area_idx].lower()
                    if any(word in context for word in ['total', 'plot area', 'land area', 'project area']):
                        # Normalize to sq ft
                        value = area['value']
                        unit = area['unit']
                        if unit == 'sq_m':
                            value *= 10.764  # Convert to sq ft
                        elif unit == 'acres':
                            value *= 43560
                        elif unit == 'hectares':
                            value *= 107639
                        metadata.total_area_sqft = value
                        break
        
        # Extract reference numbers
        metadata.reference_numbers = self.extract_reference_numbers(text)
        
        # Try to extract approval number
        if metadata.reference_numbers:
            for ref in metadata.reference_numbers:
                ref_idx = text.lower().find(ref.lower())
                if ref_idx > 0:
                    context = text[max(0, ref_idx-50):ref_idx].lower()
                    if any(word in context for word in ['approval', 'permission', 'license', 'registration']):
                        metadata.approval_number = ref
                        break
        
        # Extract issuing authority
        authority_patterns = [
            r'issued\s+by\s*:?\s*([A-Za-z\s]+?)(?:\n|$)',
            r'authority\s*:?\s*([A-Za-z\s]+?)(?:\n|$)',
            r'(?:signed|certified)\s+by\s*:?\s*([A-Za-z\s]+?)(?:\n|$)',
        ]
        
        import re
        for pattern in authority_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata.issuing_authority = match.group(1).strip()
                break
        
        return metadata
    
    def process_batch(self, pdf_paths: list[Path]) -> list[ProcessingResult]:
        """
        Process multiple PDF files.
        
        Args:
            pdf_paths: List of PDF file paths
            
        Returns:
            List of ProcessingResult objects
        """
        results = []
        for pdf_path in pdf_paths:
            try:
                result = self.process(pdf_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch processing failed for {pdf_path}: {e}")
                results.append(ProcessingResult(
                    file_path=str(pdf_path),
                    filename=pdf_path.name,
                    file_size_bytes=0,
                    page_count=0,
                    document_type=DocumentType.UNKNOWN,
                    document_type_confidence=0.0,
                    extracted_text="",
                    text_length=0,
                    metadata=ExtractedMetadata(),
                    processor_name=self.name,
                    processor_version=self.version,
                    success=False,
                    error=str(e)
                ))
        
        return results
