"""
Base Schema for Document Extraction

Common fields and utilities for all document extraction schemas.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process"""
    extracted_at: datetime = Field(default_factory=datetime.now)
    extraction_method: str = Field(default="llm", description="Method used: 'llm', 'regex', 'manual'")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall extraction confidence")
    source_file: Optional[str] = Field(None, description="Source PDF/image filename")
    ocr_engine: Optional[str] = Field(None, description="OCR engine used")
    llm_model: Optional[str] = Field(None, description="LLM model used for extraction")
    warnings: List[str] = Field(default_factory=list, description="Extraction warnings")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BaseExtractionSchema(BaseModel):
    """Base schema for all document extractions"""
    
    # Identification
    document_type: str = Field(..., description="Type of document")
    rera_registration_number: Optional[str] = Field(None, description="RERA registration number if found")
    
    # Extraction metadata
    extraction_metadata: ExtractionMetadata = Field(default_factory=ExtractionMetadata)
    
    # Raw data
    raw_text_snippet: Optional[str] = Field(None, description="First 500 chars of OCR text")
    
    # Validation
    is_valid: bool = Field(default=True, description="Whether extraction passed validation")
    validation_errors: List[str] = Field(default_factory=list)
    
    class Config:
        extra = "allow"  # Allow additional fields
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in self.dict().items() if v is not None}
    
    def get_field_confidence(self, field_name: str) -> float:
        """Get confidence for a specific field (to be overridden)"""
        return self.extraction_metadata.confidence
    
    def validate_extraction(self) -> bool:
        """Validate the extraction (to be overridden by subclasses)"""
        return True
