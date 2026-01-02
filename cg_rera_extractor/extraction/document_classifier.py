"""
Document Classifier

Identifies document type from OCR text and filename.
Supports 8 primary RERA document types.
"""

import re
import logging
from enum import Enum
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Supported RERA document types"""
    REGISTRATION_CERTIFICATE = "registration_certificate"
    LAYOUT_PLAN = "layout_plan"
    SANCTIONED_PLAN = "sanctioned_plan"
    BANK_PASSBOOK = "bank_passbook"
    ENCUMBRANCE_CERTIFICATE = "encumbrance_certificate"
    COMPLETION_CERTIFICATE = "completion_certificate"
    BUILDING_PLAN = "building_plan"
    NOC_DOCUMENT = "noc_document"
    FINANCIAL_STATEMENT = "financial_statement"
    LAND_DOCUMENT = "land_document"
    FEE_SHEET = "fee_sheet"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_string(cls, value: str) -> "DocumentType":
        """Convert string to DocumentType"""
        value = value.lower().replace(" ", "_").replace("-", "_")
        for member in cls:
            if member.value == value:
                return member
        return cls.UNKNOWN


@dataclass
class ClassificationResult:
    """Result of document classification"""
    document_type: DocumentType
    confidence: float
    matched_keywords: List[str]
    filename_match: bool
    method: str  # 'filename', 'keywords', 'llm'


# Filename patterns for document type identification
FILENAME_PATTERNS: Dict[DocumentType, List[str]] = {
    DocumentType.REGISTRATION_CERTIFICATE: [
        r"reg.*cert", r"registration", r"rera.*cert",
    ],
    DocumentType.LAYOUT_PLAN: [
        r"layout", r"site.*plan", r"plot.*plan", r"master.*plan",
    ],
    DocumentType.SANCTIONED_PLAN: [
        r"sanction", r"approved.*plan", r"approval",
    ],
    DocumentType.BANK_PASSBOOK: [
        r"passbook", r"bank.*account", r"account.*statement",
    ],
    DocumentType.ENCUMBRANCE_CERTIFICATE: [
        r"encumbrance", r"enc.*cert", r"enum", r"non.*enc",
    ],
    DocumentType.COMPLETION_CERTIFICATE: [
        r"completion", r"occupancy", r"cc\d*", r"oc\d*",
    ],
    DocumentType.BUILDING_PLAN: [
        r"building.*plan", r"floor.*plan", r"elevation",
    ],
    DocumentType.NOC_DOCUMENT: [
        r"noc", r"no.*objection", r"clearance",
    ],
    DocumentType.FINANCIAL_STATEMENT: [
        r"financial", r"balance.*sheet", r"audit", r"accounts",
    ],
    DocumentType.LAND_DOCUMENT: [
        r"land.*doc", r"khasra", r"khatauni", r"registry", r"sale.*deed",
    ],
    DocumentType.FEE_SHEET: [
        r"fee.*sheet", r"feesheet", r"fee.*calc", r"payment",
    ],
}

# Content keywords for document type identification
CONTENT_KEYWORDS: Dict[DocumentType, List[str]] = {
    DocumentType.REGISTRATION_CERTIFICATE: [
        "registration certificate",
        "rera registration",
        "registered under",
        "registration number",
        "pcgrera",
        "certificate of registration",
        "validity period",
        "real estate regulatory authority",
        "hereby certifies",
    ],
    DocumentType.LAYOUT_PLAN: [
        "layout plan",
        "plot numbers",
        "road width",
        "open space",
        "green belt",
        "plot area",
        "total plots",
        "site plan",
        "proposed layout",
        "land use plan",
    ],
    DocumentType.SANCTIONED_PLAN: [
        "sanctioned plan",
        "approved plan",
        "sanction number",
        "development authority",
        "town planning",
        "nagar palika",
        "municipal corporation",
        "approved layout",
        "permission granted",
    ],
    DocumentType.BANK_PASSBOOK: [
        "account number",
        "ifsc code",
        "bank name",
        "branch",
        "passbook",
        "current account",
        "savings account",
        "opening balance",
        "escrow account",
    ],
    DocumentType.ENCUMBRANCE_CERTIFICATE: [
        "encumbrance certificate",
        "non encumbrance",
        "free from encumbrance",
        "search report",
        "title clear",
        "no mortgage",
        "registrar office",
        "sub registrar",
    ],
    DocumentType.COMPLETION_CERTIFICATE: [
        "completion certificate",
        "occupancy certificate",
        "building complete",
        "construction completed",
        "ready for occupation",
        "partial completion",
        "final completion",
    ],
    DocumentType.BUILDING_PLAN: [
        "building plan",
        "floor plan",
        "elevation",
        "section",
        "ground floor",
        "first floor",
        "staircase",
        "parking",
        "setback",
        "plinth level",
    ],
    DocumentType.NOC_DOCUMENT: [
        "no objection certificate",
        "noc",
        "clearance certificate",
        "fire noc",
        "environment clearance",
        "pollution control",
        "airport authority",
        "highway authority",
    ],
    DocumentType.FINANCIAL_STATEMENT: [
        "balance sheet",
        "profit and loss",
        "auditor report",
        "chartered accountant",
        "financial year",
        "assets and liabilities",
        "income statement",
        "audit report",
    ],
    DocumentType.LAND_DOCUMENT: [
        "sale deed",
        "registry",
        "khasra",
        "khatauni",
        "land record",
        "mutation",
        "diversion order",
        "land conversion",
        "revenue record",
    ],
    DocumentType.FEE_SHEET: [
        "fee calculation",
        "fee sheet",
        "registration fee",
        "processing fee",
        "application fee",
        "total fee",
        "payment details",
    ],
}


class DocumentClassifier:
    """
    Classify RERA documents by type.
    
    Uses multi-stage classification:
    1. Filename pattern matching (fastest)
    2. Content keyword analysis
    3. LLM classification (fallback for ambiguous cases)
    
    Usage:
        classifier = DocumentClassifier()
        result = classifier.classify(ocr_text, "Reg_Certi_123.pdf")
        print(result.document_type)  # DocumentType.REGISTRATION_CERTIFICATE
    """
    
    def __init__(self, use_llm_fallback: bool = True):
        """
        Initialize classifier.
        
        Args:
            use_llm_fallback: Use LLM for ambiguous classifications
        """
        self.use_llm_fallback = use_llm_fallback
    
    def classify(
        self,
        text: str,
        filename: Optional[str] = None
    ) -> ClassificationResult:
        """
        Classify document type.
        
        Args:
            text: OCR-extracted text content
            filename: Original filename (optional but helpful)
            
        Returns:
            ClassificationResult with document type and confidence
        """
        # Step 1: Try filename classification
        if filename:
            result = self._classify_by_filename(filename)
            if result.confidence >= 0.8:
                logger.info(f"Classified by filename: {result.document_type.value}")
                return result
        
        # Step 2: Keyword-based classification
        keyword_result = self._classify_by_keywords(text)
        
        # If filename gave a result, combine with keyword result
        if filename and result.confidence > 0:
            combined = self._combine_results(result, keyword_result)
            if combined.confidence >= 0.7:
                return combined
        
        # If keyword result is confident enough
        if keyword_result.confidence >= 0.7:
            logger.info(f"Classified by keywords: {keyword_result.document_type.value}")
            return keyword_result
        
        # Step 3: LLM fallback (if enabled and available)
        if self.use_llm_fallback and keyword_result.confidence < 0.5:
            llm_result = self._classify_by_llm(text, filename)
            if llm_result and llm_result.confidence > keyword_result.confidence:
                return llm_result
        
        # Return best result we have
        return keyword_result
    
    def _classify_by_filename(self, filename: str) -> ClassificationResult:
        """Classify based on filename patterns"""
        filename_lower = filename.lower()
        
        for doc_type, patterns in FILENAME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    return ClassificationResult(
                        document_type=doc_type,
                        confidence=0.9,
                        matched_keywords=[pattern],
                        filename_match=True,
                        method="filename"
                    )
        
        return ClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=0.0,
            matched_keywords=[],
            filename_match=False,
            method="filename"
        )
    
    def _classify_by_keywords(self, text: str) -> ClassificationResult:
        """Classify based on content keywords"""
        text_lower = text.lower()
        
        scores: Dict[DocumentType, Tuple[float, List[str]]] = {}
        
        for doc_type, keywords in CONTENT_KEYWORDS.items():
            matched = []
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matched.append(keyword)
            
            if matched:
                # Score based on percentage of keywords matched
                # and the total number of matches
                match_ratio = len(matched) / len(keywords)
                # Bonus for more absolute matches
                absolute_bonus = min(len(matched) * 0.05, 0.2)
                score = match_ratio * 0.8 + absolute_bonus
                scores[doc_type] = (score, matched)
        
        if not scores:
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                matched_keywords=[],
                filename_match=False,
                method="keywords"
            )
        
        # Get best match
        best_type = max(scores.keys(), key=lambda k: scores[k][0])
        best_score, matched_keywords = scores[best_type]
        
        return ClassificationResult(
            document_type=best_type,
            confidence=min(best_score, 1.0),
            matched_keywords=matched_keywords,
            filename_match=False,
            method="keywords"
        )
    
    def _classify_by_llm(
        self,
        text: str,
        filename: Optional[str]
    ) -> Optional[ClassificationResult]:
        """Use LLM for classification (fallback)"""
        try:
            from ai.llm.adapter import run
            
            # Truncate text if too long
            text_sample = text[:2000] if len(text) > 2000 else text
            
            prompt = f"""Classify this RERA (Real Estate Regulatory Authority) document.

Document types to choose from:
1. registration_certificate - RERA Registration Certificate
2. layout_plan - Site/Plot Layout Plan
3. sanctioned_plan - Government Sanctioned/Approved Plan
4. bank_passbook - Bank Account Passbook/Statement
5. encumbrance_certificate - Encumbrance/Title Certificate
6. completion_certificate - Building Completion/Occupancy Certificate
7. building_plan - Building Floor/Elevation Plans
8. noc_document - No Objection Certificates
9. financial_statement - Financial Statements/Audit Reports
10. land_document - Land Records/Registry Documents
11. fee_sheet - Fee Calculation Sheet
12. unknown - Cannot determine

Filename: {filename or 'Not provided'}

Document text (first 2000 chars):
{text_sample}

Respond with ONLY the document type (e.g., "registration_certificate") and nothing else.
"""
            
            result = run(prompt, system="You are a document classifier. Respond with only the document type.", temperature=0.1)
            
            if result.get("error"):
                return None
            
            response = result.get("text", "").strip().lower()
            doc_type = DocumentType.from_string(response)
            
            return ClassificationResult(
                document_type=doc_type,
                confidence=0.75 if doc_type != DocumentType.UNKNOWN else 0.2,
                matched_keywords=[],
                filename_match=False,
                method="llm"
            )
            
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            return None
    
    def _combine_results(
        self,
        filename_result: ClassificationResult,
        keyword_result: ClassificationResult
    ) -> ClassificationResult:
        """Combine filename and keyword results"""
        # If they agree, boost confidence
        if filename_result.document_type == keyword_result.document_type:
            combined_confidence = min(
                filename_result.confidence * 0.5 + keyword_result.confidence * 0.5 + 0.2,
                1.0
            )
            return ClassificationResult(
                document_type=filename_result.document_type,
                confidence=combined_confidence,
                matched_keywords=keyword_result.matched_keywords,
                filename_match=True,
                method="combined"
            )
        
        # If they disagree, prefer filename if highly confident
        if filename_result.confidence >= 0.8:
            return filename_result
        
        # Otherwise prefer keywords
        return keyword_result
    
    def classify_batch(
        self,
        documents: List[Dict[str, str]]
    ) -> List[ClassificationResult]:
        """
        Classify multiple documents.
        
        Args:
            documents: List of dicts with 'text' and optional 'filename'
            
        Returns:
            List of ClassificationResult
        """
        results = []
        for doc in documents:
            result = self.classify(
                text=doc.get("text", ""),
                filename=doc.get("filename")
            )
            results.append(result)
        return results
    
    def get_extraction_schema(self, doc_type: DocumentType) -> Optional[str]:
        """
        Get the appropriate extraction schema for a document type.
        
        Args:
            doc_type: DocumentType enum value
            
        Returns:
            Schema module name or None
        """
        schema_mapping = {
            DocumentType.REGISTRATION_CERTIFICATE: "registration_certificate",
            DocumentType.LAYOUT_PLAN: "layout_plan",
            DocumentType.BANK_PASSBOOK: "bank_passbook",
            DocumentType.ENCUMBRANCE_CERTIFICATE: "encumbrance_certificate",
            DocumentType.SANCTIONED_PLAN: "sanctioned_plan",
            DocumentType.COMPLETION_CERTIFICATE: "completion_certificate",
            DocumentType.BUILDING_PLAN: "building_plan",
            DocumentType.NOC_DOCUMENT: "noc_document",
        }
        return schema_mapping.get(doc_type)


# Convenience function
def classify_document(text: str, filename: Optional[str] = None) -> DocumentType:
    """
    Quick classification of a document.
    
    Args:
        text: OCR text
        filename: Original filename
        
    Returns:
        DocumentType enum value
    """
    classifier = DocumentClassifier()
    result = classifier.classify(text, filename)
    return result.document_type
