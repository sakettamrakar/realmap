"""
Base classes and types for PDF Processing.

Provides abstract base class and common types used by all PDF processors.
"""
from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Enumeration of recognized RERA document types."""
    
    REGISTRATION_CERTIFICATE = "registration_certificate"
    BUILDING_PERMISSION = "building_permission"
    LAYOUT_PLAN = "layout_plan"
    NOC_FIRE = "noc_fire"
    NOC_ENVIRONMENT = "noc_environment"
    NOC_POLLUTION = "noc_pollution"
    NOC_WATER = "noc_water"
    NOC_OTHER = "noc_other"
    COST_DESCRIPTION = "cost_description"
    AGREEMENT = "agreement"
    AFFIDAVIT = "affidavit"
    CA_CERTIFICATE = "ca_certificate"
    ENGINEER_CERTIFICATE = "engineer_certificate"
    QUARTERLY_REPORT = "quarterly_report"
    BANK_PASSBOOK = "bank_passbook"
    SEARCH_REPORT = "search_report"
    ENCUMBRANCE_CERTIFICATE = "encumbrance_certificate"
    DEVELOPMENT_PLAN = "development_plan"
    PROJECT_SPECIFICATION = "project_specification"
    OTHER = "other"
    UNKNOWN = "unknown"


# Patterns for document type detection
DOCUMENT_TYPE_PATTERNS: Dict[DocumentType, List[str]] = {
    DocumentType.REGISTRATION_CERTIFICATE: [
        r"registration\s*certificate",
        r"rera\s*certificate",
        r"project\s*registration"
    ],
    DocumentType.BUILDING_PERMISSION: [
        r"building\s*permission",
        r"construction\s*permit",
        r"sanctioned\s*(building\s*)?plan",
        r"building\s*approval"
    ],
    DocumentType.LAYOUT_PLAN: [
        r"layout\s*plan",
        r"site\s*plan",
        r"master\s*plan",
        r"sanctioned\s*layout"
    ],
    DocumentType.NOC_FIRE: [
        r"fire\s*(safety\s*)?(no[c\-]?\s*objection|noc|clearance)",
        r"noc.*fire"
    ],
    DocumentType.NOC_ENVIRONMENT: [
        r"environment(al)?\s*(no[c\-]?\s*objection|noc|clearance)",
        r"noc.*environment"
    ],
    DocumentType.NOC_POLLUTION: [
        r"pollution\s*(control\s*)?(no[c\-]?\s*objection|noc|clearance)",
        r"noc.*pollution"
    ],
    DocumentType.NOC_WATER: [
        r"water\s*(supply\s*)?(no[c\-]?\s*objection|noc|clearance)",
        r"noc.*water"
    ],
    DocumentType.COST_DESCRIPTION: [
        r"cost\s*(description|estimate|sheet)",
        r"project\s*cost",
        r"financial\s*(plan|estimate)"
    ],
    DocumentType.AGREEMENT: [
        r"agreement",
        r"deed",
        r"mou",
        r"contract"
    ],
    DocumentType.AFFIDAVIT: [
        r"affidavit",
        r"declaration",
        r"undertaking"
    ],
    DocumentType.CA_CERTIFICATE: [
        r"ca\s*certificate",
        r"chartered\s*accountant",
        r"auditor.*certificate"
    ],
    DocumentType.ENGINEER_CERTIFICATE: [
        r"engineer\s*certificate",
        r"structural.*certificate"
    ],
    DocumentType.QUARTERLY_REPORT: [
        r"quarterly\s*(progress\s*)?report",
        r"qpr",
        r"progress\s*report"
    ],
    DocumentType.BANK_PASSBOOK: [
        r"bank\s*(account\s*)?passbook",
        r"account\s*statement"
    ],
    DocumentType.SEARCH_REPORT: [
        r"search\s*report",
        r"title\s*search"
    ],
    DocumentType.ENCUMBRANCE_CERTIFICATE: [
        r"encumbrance",
        r"non[-\s]?encumbrance"
    ],
    DocumentType.DEVELOPMENT_PLAN: [
        r"development\s*(work\s*)?plan",
        r"development\s*permission"
    ],
    DocumentType.PROJECT_SPECIFICATION: [
        r"project\s*specification",
        r"technical\s*specification"
    ],
}


@dataclass
class ExtractedMetadata:
    """Structured metadata extracted from a PDF."""
    
    # Dates
    dates: List[str] = field(default_factory=list)
    approval_date: Optional[str] = None
    validity_date: Optional[str] = None
    
    # Financial
    amounts: List[Dict[str, Any]] = field(default_factory=list)
    total_cost: Optional[float] = None
    
    # Area measurements
    areas: List[Dict[str, Any]] = field(default_factory=list)
    total_area_sqft: Optional[float] = None
    
    # Approval details
    approval_number: Optional[str] = None
    issuing_authority: Optional[str] = None
    validity_period: Optional[str] = None
    
    # Building details
    floor_count: Optional[int] = None
    unit_count: Optional[int] = None
    
    # Entities
    party_names: List[str] = field(default_factory=list)
    
    # Additional structured data
    key_terms: List[str] = field(default_factory=list)
    reference_numbers: List[str] = field(default_factory=list)
    
    # Summary (typically LLM-generated)
    summary: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "dates": self.dates,
            "approval_date": self.approval_date,
            "validity_date": self.validity_date,
            "amounts": self.amounts,
            "total_cost": self.total_cost,
            "areas": self.areas,
            "total_area_sqft": self.total_area_sqft,
            "approval_number": self.approval_number,
            "issuing_authority": self.issuing_authority,
            "validity_period": self.validity_period,
            "floor_count": self.floor_count,
            "unit_count": self.unit_count,
            "party_names": self.party_names,
            "key_terms": self.key_terms,
            "reference_numbers": self.reference_numbers,
            "summary": self.summary,
        }


@dataclass
class ProcessingResult:
    """Result from processing a PDF document."""
    
    # File info
    file_path: str
    filename: str
    file_size_bytes: int
    page_count: int
    
    # Classification
    document_type: DocumentType
    document_type_confidence: float
    
    # Extracted content
    extracted_text: str
    text_length: int
    
    # Structured metadata
    metadata: ExtractedMetadata
    
    # AI/LLM specific (optional)
    llm_response: Optional[Dict[str, Any]] = None
    llm_model: Optional[str] = None
    llm_tokens_used: int = 0
    
    # Processing info
    processor_name: str = "unknown"
    processor_version: str = "1.0"
    processing_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    processing_time_ms: int = 0
    
    # Status
    success: bool = True
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "filename": self.filename,
            "file_size_bytes": self.file_size_bytes,
            "page_count": self.page_count,
            "document_type": self.document_type.value,
            "document_type_confidence": self.document_type_confidence,
            "extracted_text": self.extracted_text[:1000] + "..." if len(self.extracted_text) > 1000 else self.extracted_text,
            "text_length": self.text_length,
            "metadata": self.metadata.to_dict(),
            "llm_response": self.llm_response,
            "llm_model": self.llm_model,
            "llm_tokens_used": self.llm_tokens_used,
            "processor_name": self.processor_name,
            "processor_version": self.processor_version,
            "processing_timestamp": self.processing_timestamp,
            "processing_time_ms": self.processing_time_ms,
            "success": self.success,
            "error": self.error,
            "warnings": self.warnings,
        }


class BasePDFProcessor(ABC):
    """
    Abstract base class for PDF processors.
    
    All PDF processors must inherit from this class and implement
    the process() method.
    """
    
    name: str = "base"
    version: str = "1.0"
    
    def __init__(self):
        self.logger = logging.getLogger(f"pdf_processor.{self.name}")
    
    @abstractmethod
    def process(self, pdf_path: Path) -> ProcessingResult:
        """
        Process a PDF file and return extraction results.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ProcessingResult with extracted data
        """
        pass
    
    def detect_document_type(self, text: str, filename: str) -> tuple[DocumentType, float]:
        """
        Detect document type from content and filename.
        
        Returns:
            Tuple of (DocumentType, confidence_score)
        """
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Score each document type
        scores: Dict[DocumentType, float] = {}
        
        for doc_type, patterns in DOCUMENT_TYPE_PATTERNS.items():
            score = 0.0
            for pattern in patterns:
                # Check filename (higher weight)
                if re.search(pattern, filename_lower, re.IGNORECASE):
                    score += 0.4
                # Check content (lower weight but cumulative)
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                score += len(matches) * 0.1
            
            if score > 0:
                scores[doc_type] = min(score, 1.0)  # Cap at 1.0
        
        if not scores:
            return DocumentType.UNKNOWN, 0.0
        
        # Return highest scoring type
        best_type = max(scores, key=scores.get)
        return best_type, scores[best_type]
    
    def validate_pdf(self, pdf_path: Path) -> tuple[bool, Optional[str]]:
        """
        Validate that a file is a proper PDF.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not pdf_path.exists():
            return False, f"File not found: {pdf_path}"
        
        if pdf_path.stat().st_size == 0:
            return False, "File is empty"
        
        # Check PDF header
        try:
            with open(pdf_path, 'rb') as f:
                header = f.read(5)
                if not header.startswith(b'%PDF-'):
                    return False, f"Invalid PDF header: {header}"
        except Exception as e:
            return False, f"Error reading file: {e}"
        
        return True, None
    
    def extract_dates(self, text: str) -> List[str]:
        """Extract dates in various formats from text."""
        patterns = [
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
        ]
        
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return list(set(dates))
    
    def extract_amounts(self, text: str) -> List[Dict[str, Any]]:
        """Extract monetary amounts from text."""
        patterns = [
            (r'₹\s*([\d,]+(?:\.\d{2})?)', 'INR'),
            (r'Rs\.?\s*([\d,]+(?:\.\d{2})?)', 'INR'),
            (r'INR\s*([\d,]+(?:\.\d{2})?)', 'INR'),
            (r'([\d,]+(?:\.\d{2})?)\s*(?:rupees|lakhs?|crores?)', 'INR'),
        ]
        
        amounts = []
        for pattern, currency in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                    # Check context for lakhs/crores
                    context = text[max(0, match.start()-20):match.end()+20].lower()
                    if 'crore' in context:
                        amount *= 10_000_000
                    elif 'lakh' in context:
                        amount *= 100_000
                    
                    amounts.append({
                        'amount': amount,
                        'currency': currency,
                        'raw': match.group(0)
                    })
                except ValueError:
                    continue
        
        return amounts
    
    def extract_areas(self, text: str) -> List[Dict[str, Any]]:
        """Extract area measurements from text."""
        patterns = [
            (r'([\d,]+\.?\d*)\s*(?:sq\.?\s*(?:ft|feet))', 'sq_ft'),
            (r'([\d,]+\.?\d*)\s*(?:square\s+feet)', 'sq_ft'),
            (r'([\d,]+\.?\d*)\s*(?:sq\.?\s*(?:m|meter|metre))', 'sq_m'),
            (r'([\d,]+\.?\d*)\s*(?:square\s+meter)', 'sq_m'),
            (r'([\d,]+\.?\d*)\s*(?:acres?)', 'acres'),
            (r'([\d,]+\.?\d*)\s*(?:hectares?)', 'hectares'),
        ]
        
        areas = []
        for pattern, unit in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                value_str = match.group(1).replace(',', '')
                try:
                    areas.append({
                        'value': float(value_str),
                        'unit': unit,
                        'raw': match.group(0)
                    })
                except ValueError:
                    continue
        
        return areas
    
    def extract_reference_numbers(self, text: str) -> List[str]:
        """Extract reference/approval numbers from text."""
        patterns = [
            r'(?:approval|license|permission|registration)\s*(?:no\.?|number)\s*:?\s*([A-Z0-9\-/]+)',
            r'(?:ref\.?|reference)\s*(?:no\.?|number)\s*:?\s*([A-Z0-9\-/]+)',
            r'RERA[A-Z]*\d+',
            r'[A-Z]{2,}[-/]\d{2,}[-/]\d+',
        ]
        
        refs = []
        for pattern in patterns:
            refs.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return list(set(refs))
