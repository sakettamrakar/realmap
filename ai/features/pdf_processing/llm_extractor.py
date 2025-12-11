"""
LLM-based PDF Extractor.

Uses the local LLM (llama-cpp-python) for intelligent document analysis.
Provides deeper semantic understanding than text-only extraction.
"""
from __future__ import annotations

import json
import logging
import re
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


# ============================================================================
# LLM PROMPTS
# ============================================================================

DOCUMENT_CLASSIFICATION_PROMPT = """Classify this document into exactly ONE category.

Categories:
REGISTRATION - Registration certificate, RERA certificate
BUILDING_PERMISSION - Building/construction approval
LAYOUT_PLAN - Layout or site plan
CA_CERTIFICATE - Chartered Accountant certificate, financial certificate
NOC_FIRE - Fire department NOC
NOC_ENVIRONMENT - Environmental clearance
NOC_OTHER - Other NOC documents
AGREEMENT - Contracts, MOUs
BANK_PASSBOOK - Bank account documents
SEARCH_REPORT - Search report
ENCUMBRANCE - Encumbrance certificate
PROJECT_SPECIFICATION - Project specifications
DEVELOPMENT_PLAN - Development plans
ENGINEER_CERTIFICATE - Engineer certificate
OTHER - Other documents

Document text:
{text}

Category:"""


METADATA_EXTRACTION_PROMPT = """Extract information from this {document_type} document as JSON.

Document:
{text}

Extract these fields (use null if not found):
- approval_number: certificate/registration number (actual number, not description)
- approval_date: date in YYYY-MM-DD format (actual date, not placeholder)  
- issuing_authority: authority name
- total_area_sqft: area in sqft (number only)
- total_cost: cost in rupees (number only)

Return JSON with actual values found in the document. Use null for anything not found.

JSON:
{{"""


DOCUMENT_SUMMARY_PROMPT = """Summarize this document in 2-3 sentences. Focus on:
- What type of document it is
- Key approvals or permissions granted
- Important dates and numbers
- Any conditions or restrictions

Document text (first 3000 characters):
{text}

Summary:"""


# ============================================================================
# LLM EXTRACTOR
# ============================================================================

class LLMExtractor(BasePDFProcessor):
    """
    LLM-based PDF processor using local language model.
    
    Features:
    - Semantic document classification
    - Intelligent metadata extraction
    - Context-aware information parsing
    - Document summarization
    
    Requirements:
    - LLM model loaded via ai.llm.adapter
    - pypdf for text extraction
    
    Usage:
        extractor = LLMExtractor()
        result = extractor.process(Path("document.pdf"))
        print(f"Type: {result.document_type}")
        print(f"Summary: {result.metadata.summary}")
    """
    
    name = "llm_extractor"
    version = "1.0"
    
    def __init__(
        self,
        max_pages: int = 10,
        max_tokens: int = 256,
        temperature: float = 0.3,
        fallback_to_text: bool = True
    ):
        """
        Initialize LLM extractor.
        
        Args:
            max_pages: Maximum pages to process (default: 10)
            max_tokens: Max tokens for LLM response (default: 512)
            temperature: LLM temperature (default: 0.3 for consistency)
            fallback_to_text: Fall back to text extraction if LLM fails
        """
        super().__init__()
        self.max_pages = max_pages
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.fallback_to_text = fallback_to_text
        
        if not HAS_PYPDF:
            raise ImportError(
                "pypdf is required for LLMExtractor. "
                "Install with: pip install pypdf"
            )
        
        # Import LLM adapter
        try:
            from ai.llm.adapter import run as llm_run, get_llm_instance
            self._llm_run = llm_run
            self._get_llm = get_llm_instance
        except ImportError:
            logger.warning("LLM adapter not available, will use mock responses")
            self._llm_run = None
            self._get_llm = None
    
    def _call_llm(
        self,
        prompt: str,
        system: str = "",
        max_tokens: Optional[int] = None
    ) -> tuple[str, int, int]:
        """
        Call the LLM and return response.
        
        Returns:
            Tuple of (response_text, tokens_used, latency_ms)
        """
        if not self._llm_run:
            return "", 0, 0
        
        tokens = max_tokens or self.max_tokens
        
        result = self._llm_run(
            prompt=prompt,
            system=system,
            max_tokens=tokens,
            temperature=self.temperature
        )
        
        if result.get("error"):
            logger.warning(f"LLM call failed: {result['error']}")
            return "", result.get("tokens_used", 0), result.get("latency_ms", 0)
        
        return (
            result.get("text", "").strip(),
            result.get("tokens_used", 0),
            result.get("latency_ms", 0)
        )
    
    def _classify_with_llm(self, text: str) -> tuple[DocumentType, float]:
        """
        Classify document using LLM.
        
        Returns:
            Tuple of (DocumentType, confidence)
        """
        # Truncate text for classification
        truncated_text = text[:2000]
        prompt = DOCUMENT_CLASSIFICATION_PROMPT.format(text=truncated_text)
        
        response, _, _ = self._call_llm(prompt, max_tokens=50)
        
        if not response:
            # Fall back to rule-based detection
            return self.detect_document_type(text, "")
        
        # Parse response
        response_upper = response.upper().strip()
        
        # Map response to DocumentType - match LLM output to enum values
        type_mapping = {
            "REGISTRATION": DocumentType.REGISTRATION_CERTIFICATE,
            "BUILDING_PERMISSION": DocumentType.BUILDING_PERMISSION,
            "LAYOUT_PLAN": DocumentType.LAYOUT_PLAN,
            "CA_CERTIFICATE": DocumentType.CA_CERTIFICATE,
            "FINANCIAL": DocumentType.CA_CERTIFICATE,  # Alias
            "NOC_FIRE": DocumentType.NOC_FIRE,
            "NOC_ENVIRONMENT": DocumentType.NOC_ENVIRONMENT,
            "NOC_OTHER": DocumentType.NOC_OTHER,
            "NOC": DocumentType.NOC_OTHER,  # Fallback for generic NOC
            "AGREEMENT": DocumentType.AGREEMENT,
            "BANK_PASSBOOK": DocumentType.BANK_PASSBOOK,
            "BANK": DocumentType.BANK_PASSBOOK,  # Alias
            "SEARCH_REPORT": DocumentType.SEARCH_REPORT,
            "ENCUMBRANCE": DocumentType.ENCUMBRANCE_CERTIFICATE,
            "PROJECT_SPECIFICATION": DocumentType.PROJECT_SPECIFICATION,
            "SPECIFICATION": DocumentType.PROJECT_SPECIFICATION,  # Alias
            "DEVELOPMENT_PLAN": DocumentType.DEVELOPMENT_PLAN,
            "DEVELOPMENT": DocumentType.DEVELOPMENT_PLAN,  # Alias
            "ENGINEER_CERTIFICATE": DocumentType.ENGINEER_CERTIFICATE,
            "ENGINEER": DocumentType.ENGINEER_CERTIFICATE,  # Alias
            "OTHER": DocumentType.OTHER,
        }
        
        for key, doc_type in type_mapping.items():
            if key in response_upper:
                return doc_type, 0.85  # LLM classification confidence
        
        return DocumentType.UNKNOWN, 0.3
    
    def _extract_metadata_with_llm(
        self,
        text: str,
        doc_type: DocumentType
    ) -> ExtractedMetadata:
        """
        Extract metadata using LLM.
        
        Returns:
            ExtractedMetadata with LLM-extracted fields
        """
        metadata = ExtractedMetadata()
        
        # Truncate text for extraction
        truncated_text = text[:3000]
        prompt = METADATA_EXTRACTION_PROMPT.format(
            document_type=doc_type.value,
            text=truncated_text
        )
        
        response, _, _ = self._call_llm(
            prompt,
            system="Extract document information as JSON only.",
            max_tokens=self.max_tokens
        )
        
        if not response:
            # Fall back to regex extraction
            return self._extract_metadata_regex(text)
        
        # Try to parse JSON response
        try:
            # The prompt ends with "{" so we need to prepend it
            json_str = "{" + response.strip()
            
            # Clean up response - find JSON in response
            json_match = re.search(r'\{[^{}]*\}', json_str)
            if json_match:
                data = json.loads(json_match.group())
            else:
                # Try full response
                data = json.loads(json_str)
            
            # Map extracted data to metadata
            if data.get("approval_number"):
                metadata.approval_number = str(data["approval_number"])
                metadata.reference_numbers = [metadata.approval_number]
            
            if data.get("approval_date"):
                metadata.approval_date = str(data["approval_date"])
                metadata.dates = [metadata.approval_date]
            
            if data.get("validity_date"):
                metadata.validity_date = str(data["validity_date"])
                if metadata.dates:
                    metadata.dates.append(metadata.validity_date)
                else:
                    metadata.dates = [metadata.validity_date]
            
            if data.get("issuing_authority"):
                metadata.issuing_authority = str(data["issuing_authority"])
            
            if data.get("total_area_sqft") and isinstance(data["total_area_sqft"], (int, float)):
                metadata.total_area_sqft = float(data["total_area_sqft"])
            
            if data.get("total_cost") and isinstance(data["total_cost"], (int, float)):
                metadata.total_cost = float(data["total_cost"])
            
            if data.get("floor_count") and isinstance(data["floor_count"], int):
                metadata.floor_count = data["floor_count"]
            
            if data.get("unit_count") and isinstance(data["unit_count"], int):
                metadata.unit_count = data["unit_count"]
            
            if data.get("summary"):
                metadata.summary = str(data["summary"])
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            # Fall back to regex
            return self._extract_metadata_regex(text)
        
        return metadata
    
    def _extract_metadata_regex(self, text: str) -> ExtractedMetadata:
        """Fallback regex-based metadata extraction."""
        metadata = ExtractedMetadata()
        
        # Use base class methods
        metadata.dates = self.extract_dates(text)
        metadata.amounts = self.extract_amounts(text)
        metadata.areas = self.extract_areas(text)
        metadata.reference_numbers = self.extract_reference_numbers(text)
        
        return metadata
    
    def _generate_summary(self, text: str) -> str:
        """Generate document summary using LLM."""
        truncated_text = text[:3000]
        prompt = DOCUMENT_SUMMARY_PROMPT.format(text=truncated_text)
        
        response, _, _ = self._call_llm(prompt, max_tokens=200)
        
        return response if response else ""
    
    def process(self, pdf_path: Path) -> ProcessingResult:
        """
        Process a PDF file using LLM for analysis.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ProcessingResult with LLM-extracted data
        """
        start_time = time.time()
        total_tokens = 0
        total_llm_latency = 0
        
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
                
                if len(reader.pages) > self.max_pages:
                    result.warnings.append(
                        f"Truncated: processed {self.max_pages} of {len(reader.pages)} pages"
                    )
            
            result.extracted_text = "\n\n".join(text_parts)
            result.text_length = len(result.extracted_text)
            
            if result.text_length < 50:
                result.warnings.append(
                    "Very little text extracted - PDF may be scanned/image-based"
                )
            
            # Check if LLM is available
            llm_available = self._get_llm and self._get_llm() is not None
            
            # Skip LLM for documents with no text - use rule-based detection instead
            if llm_available and result.text_length >= 50:
                # Use LLM for classification
                doc_type, confidence = self._classify_with_llm(result.extracted_text)
                result.document_type = doc_type
                result.document_type_confidence = confidence
                
                # Use LLM for metadata extraction only if we have text
                result.metadata = self._extract_metadata_with_llm(
                    result.extracted_text,
                    doc_type
                )
                
                # Generate summary if not already present
                if not result.metadata.summary:
                    result.metadata.summary = self._generate_summary(result.extracted_text)
            else:
                # Fall back to rule-based detection for empty/minimal text
                if not llm_available:
                    logger.info("LLM not available, using rule-based extraction")
                    result.warnings.append("LLM not available - using rule-based extraction")
                else:
                    logger.info("Insufficient text for LLM, using rule-based extraction")
                    
                doc_type, confidence = self.detect_document_type(
                    result.extracted_text,
                    pdf_path.name
                )
                result.document_type = doc_type
                result.document_type_confidence = confidence
                
                # Use regex-based metadata extraction
                result.metadata = self._extract_metadata_regex(result.extracted_text)
            
            result.success = True
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            logger.error(f"Failed to process {pdf_path}: {e}")
            
            if self.fallback_to_text:
                logger.info("Falling back to text-only extraction")
                try:
                    from .text_extractor import TextExtractor
                    text_extractor = TextExtractor(max_pages=self.max_pages)
                    return text_extractor.process(pdf_path)
                except Exception as fallback_error:
                    result.warnings.append(f"Fallback also failed: {fallback_error}")
        
        # Record processing time
        result.processing_time_ms = int((time.time() - start_time) * 1000)
        
        return result
    
    def process_batch(self, pdf_paths: list[Path]) -> list[ProcessingResult]:
        """
        Process multiple PDF files with LLM.
        
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
