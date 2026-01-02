"""
LLM-Based Structured Data Extractor

Uses local LLM (via ai/llm/adapter.py) to extract structured data
from OCR text based on document type-specific prompts.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Type
from dataclasses import dataclass
from datetime import datetime

from .document_classifier import DocumentType
from .schemas.base import BaseExtractionSchema, ExtractionMetadata
from .schemas.registration_certificate import RegistrationCertificateSchema
from .schemas.layout_plan import LayoutPlanSchema
from .schemas.bank_passbook import BankPassbookSchema
from .schemas.encumbrance_certificate import EncumbranceCertificateSchema
from .schemas.sanctioned_plan import SanctionedPlanSchema
from .schemas.completion_certificate import CompletionCertificateSchema
from .schemas.building_plan import BuildingPlanSchema

logger = logging.getLogger(__name__)

# Mapping of document types to schemas
SCHEMA_MAPPING: Dict[DocumentType, Type[BaseExtractionSchema]] = {
    DocumentType.REGISTRATION_CERTIFICATE: RegistrationCertificateSchema,
    DocumentType.LAYOUT_PLAN: LayoutPlanSchema,
    DocumentType.BANK_PASSBOOK: BankPassbookSchema,
    DocumentType.ENCUMBRANCE_CERTIFICATE: EncumbranceCertificateSchema,
    DocumentType.SANCTIONED_PLAN: SanctionedPlanSchema,
    DocumentType.COMPLETION_CERTIFICATE: CompletionCertificateSchema,
    DocumentType.BUILDING_PLAN: BuildingPlanSchema,
}

# Path to prompts directory
PROMPTS_DIR = Path(__file__).parent / "prompts"


@dataclass
class ExtractionResult:
    """Result of LLM extraction"""
    success: bool
    document_type: DocumentType
    data: Dict[str, Any]
    schema: Optional[BaseExtractionSchema]
    raw_llm_response: str
    error: Optional[str] = None
    processing_time_ms: int = 0


class LLMExtractor:
    """
    Extract structured data from OCR text using LLM.
    
    Uses the existing ai/llm/adapter for LLM calls and
    document-specific prompts for accurate extraction.
    
    Usage:
        extractor = LLMExtractor()
        result = extractor.extract(ocr_text, DocumentType.REGISTRATION_CERTIFICATE)
        if result.success:
            print(result.data)
    """
    
    def __init__(
        self,
        max_text_length: int = 6000,
        temperature: float = 0.1,
        validate_output: bool = True
    ):
        """
        Initialize LLM extractor.
        
        Args:
            max_text_length: Maximum OCR text length to send to LLM
            temperature: LLM temperature (lower = more deterministic)
            validate_output: Whether to validate against Pydantic schema
        """
        self.max_text_length = max_text_length
        self.temperature = temperature
        self.validate_output = validate_output
        self._prompts_cache: Dict[str, str] = {}
    
    def _load_prompt(self, doc_type: DocumentType) -> Optional[str]:
        """Load prompt template for document type"""
        # Check cache
        cache_key = doc_type.value
        if cache_key in self._prompts_cache:
            return self._prompts_cache[cache_key]
        
        # Load from file
        prompt_file = PROMPTS_DIR / f"{doc_type.value}.txt"
        
        if not prompt_file.exists():
            logger.warning(f"Prompt file not found: {prompt_file}")
            return None
        
        try:
            prompt = prompt_file.read_text(encoding='utf-8')
            self._prompts_cache[cache_key] = prompt
            return prompt
        except Exception as e:
            logger.error(f"Failed to load prompt: {e}")
            return None
    
    def _get_generic_prompt(self, doc_type: DocumentType) -> str:
        """Generate a generic extraction prompt for unsupported doc types"""
        return f"""
You are an expert document extraction AI.

Extract all relevant structured information from this {doc_type.value.replace('_', ' ')} document.

Look for:
- Names (people, companies, projects)
- Dates (registration, validity, approval)
- Numbers (registration numbers, amounts, areas, counts)
- Addresses and locations
- Status information

OCR Text:
```
{{ocr_text}}
```

Return a JSON object with all extracted fields.
Use null for fields you cannot find.
Include an "extraction_confidence" field (0-1) indicating your confidence.
"""
    
    def _truncate_text(self, text: str) -> str:
        """Truncate text to max length while preserving meaningful content"""
        if len(text) <= self.max_text_length:
            return text
        
        # Try to truncate at a sentence/paragraph boundary
        truncated = text[:self.max_text_length]
        
        # Find last complete sentence
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')
        
        cut_point = max(last_period, last_newline)
        if cut_point > self.max_text_length * 0.7:  # Only if we keep >70%
            truncated = truncated[:cut_point + 1]
        
        return truncated + "\n\n[Text truncated...]"
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract JSON"""
        # Try direct JSON parsing
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON in response
        # Look for {...} pattern
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Try to find ```json ... ``` block
        code_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
        if code_match:
            try:
                return json.loads(code_match.group(1))
            except json.JSONDecodeError:
                pass
        
        logger.warning("Could not parse JSON from LLM response")
        return {}
    
    def _validate_and_create_schema(
        self,
        data: Dict[str, Any],
        doc_type: DocumentType,
        source_file: Optional[str] = None
    ) -> Optional[BaseExtractionSchema]:
        """Validate extracted data against schema"""
        schema_class = SCHEMA_MAPPING.get(doc_type)
        
        if not schema_class:
            logger.warning(f"No schema for document type: {doc_type}")
            return None
        
        try:
            # Add metadata
            data['document_type'] = doc_type.value
            data['extraction_metadata'] = ExtractionMetadata(
                extraction_method='llm',
                confidence=data.get('extraction_confidence', 0.5),
                source_file=source_file,
                llm_model='local'
            )
            
            # Create schema instance
            schema = schema_class(**data)
            
            # Run validation
            schema.validate_extraction()
            
            return schema
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return None
    
    def extract(
        self,
        ocr_text: str,
        doc_type: DocumentType,
        source_file: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract structured data from OCR text.
        
        Args:
            ocr_text: Text extracted via OCR
            doc_type: Type of document
            source_file: Optional source filename for metadata
            
        Returns:
            ExtractionResult with extracted data
        """
        start_time = datetime.now()
        
        if not ocr_text or not ocr_text.strip():
            return ExtractionResult(
                success=False,
                document_type=doc_type,
                data={},
                schema=None,
                raw_llm_response="",
                error="Empty OCR text"
            )
        
        # Load prompt template
        prompt_template = self._load_prompt(doc_type)
        if not prompt_template:
            prompt_template = self._get_generic_prompt(doc_type)
        
        # Truncate text if needed
        truncated_text = self._truncate_text(ocr_text)
        
        # Format prompt
        prompt = prompt_template.replace("{ocr_text}", truncated_text)
        
        # Call LLM
        try:
            from ai.llm.adapter import run as llm_run
            
            result = llm_run(
                prompt,
                system="You are a JSON-only response bot. Extract data and return valid JSON.",
                temperature=self.temperature
            )
            
            if result.get("error"):
                return ExtractionResult(
                    success=False,
                    document_type=doc_type,
                    data={},
                    schema=None,
                    raw_llm_response=str(result),
                    error=f"LLM error: {result.get('error')}"
                )
            
            raw_response = result.get("text", "")
            
        except ImportError:
            logger.error("ai.llm.adapter not available")
            return ExtractionResult(
                success=False,
                document_type=doc_type,
                data={},
                schema=None,
                raw_llm_response="",
                error="LLM adapter not available"
            )
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return ExtractionResult(
                success=False,
                document_type=doc_type,
                data={},
                schema=None,
                raw_llm_response="",
                error=str(e)
            )
        
        # Parse response
        data = self._parse_llm_response(raw_response)
        
        if not data:
            return ExtractionResult(
                success=False,
                document_type=doc_type,
                data={},
                schema=None,
                raw_llm_response=raw_response,
                error="Failed to parse JSON from LLM response"
            )
        
        # Validate against schema
        schema = None
        if self.validate_output:
            schema = self._validate_and_create_schema(data, doc_type, source_file)
        
        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return ExtractionResult(
            success=True,
            document_type=doc_type,
            data=data,
            schema=schema,
            raw_llm_response=raw_response,
            processing_time_ms=processing_time
        )
    
    def extract_multiple(
        self,
        documents: list[Dict[str, Any]]
    ) -> list[ExtractionResult]:
        """
        Extract from multiple documents.
        
        Args:
            documents: List of dicts with 'text', 'doc_type', and optional 'filename'
            
        Returns:
            List of ExtractionResult
        """
        results = []
        
        for doc in documents:
            doc_type = doc.get('doc_type')
            if isinstance(doc_type, str):
                doc_type = DocumentType.from_string(doc_type)
            
            result = self.extract(
                ocr_text=doc.get('text', ''),
                doc_type=doc_type or DocumentType.UNKNOWN,
                source_file=doc.get('filename')
            )
            results.append(result)
        
        return results


# Convenience function
def extract_from_text(
    ocr_text: str,
    doc_type: str
) -> Dict[str, Any]:
    """
    Quick extraction from OCR text.
    
    Args:
        ocr_text: OCR text content
        doc_type: Document type string
        
    Returns:
        Extracted data dictionary
    """
    extractor = LLMExtractor()
    result = extractor.extract(
        ocr_text,
        DocumentType.from_string(doc_type)
    )
    return result.data if result.success else {}
