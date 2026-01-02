"""
Encumbrance Certificate Schema

Schema for data extracted from Encumbrance/Non-Encumbrance Certificates.
"""

from typing import Optional, List, Dict
from pydantic import Field

from .base import BaseExtractionSchema


class EncumbranceEntry(BaseExtractionSchema):
    """Individual encumbrance entry"""
    entry_type: str = Field(..., description="Type: Mortgage/Lien/Sale/Gift/etc.")
    document_number: Optional[str] = Field(None)
    registration_date: Optional[str] = Field(None)
    parties: Optional[str] = Field(None, description="Parties involved")
    details: Optional[str] = Field(None)


class EncumbranceCertificateSchema(BaseExtractionSchema):
    """
    Schema for Encumbrance Certificate extraction.
    
    Encumbrance certificates confirm whether property
    is free from legal/monetary liabilities.
    """
    
    document_type: str = Field(default="encumbrance_certificate")
    
    # Certificate Details
    certificate_number: Optional[str] = Field(None, description="Certificate number")
    issue_date: Optional[str] = Field(None, description="Issue date (YYYY-MM-DD)")
    issuing_authority: Optional[str] = Field(None, description="Sub-Registrar office")
    
    # Property Details
    property_description: Optional[str] = Field(None, description="Property description")
    survey_numbers: List[str] = Field(
        default_factory=list,
        description="Khasra/Survey numbers"
    )
    area: Optional[str] = Field(None, description="Property area")
    village: Optional[str] = Field(None, description="Village name")
    tehsil: Optional[str] = Field(None, description="Tehsil name")
    district: Optional[str] = Field(None, description="District name")
    
    # Search Period
    search_from_date: Optional[str] = Field(None, description="Search period start (YYYY-MM-DD)")
    search_to_date: Optional[str] = Field(None, description="Search period end (YYYY-MM-DD)")
    search_period_years: Optional[int] = Field(None, description="Number of years searched")
    
    # Encumbrance Status
    is_clear: bool = Field(
        default=True,
        description="Whether property is free from encumbrances"
    )
    encumbrance_status: Optional[str] = Field(
        default="Clear",
        description="Status: Clear/Encumbered/Partial"
    )
    
    # Encumbrance Details (if any)
    encumbrances: List[Dict] = Field(
        default_factory=list,
        description="List of encumbrances if any"
    )
    
    # Owner Details
    current_owner: Optional[str] = Field(None, description="Current owner name")
    previous_owners: List[str] = Field(
        default_factory=list,
        description="Previous owner names"
    )
    
    # Transactions (if listed)
    transaction_count: Optional[int] = Field(None, description="Number of transactions in period")
    
    def validate_extraction(self) -> bool:
        """Validate encumbrance certificate extraction"""
        errors = []
        
        if not self.survey_numbers and not self.property_description:
            errors.append("Missing property identification")
        
        if not self.search_from_date and not self.search_to_date:
            errors.append("Missing search period")
        
        self.validation_errors = errors
        self.is_valid = len(errors) == 0
        return self.is_valid


# Import Dict for type hint
from typing import Dict
