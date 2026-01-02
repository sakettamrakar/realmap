"""
Completion Certificate Schema

Schema for data extracted from Building Completion/Occupancy Certificates.
"""

from typing import Optional, List
from pydantic import Field

from .base import BaseExtractionSchema


class CompletionCertificateSchema(BaseExtractionSchema):
    """
    Schema for Completion Certificate extraction.
    
    Issued when construction is complete and building
    is ready for occupation.
    """
    
    document_type: str = Field(default="completion_certificate")
    
    # Certificate Details
    certificate_number: Optional[str] = Field(None, description="Certificate number")
    certificate_type: Optional[str] = Field(
        None, 
        description="Type: Full Completion/Partial Completion/Occupancy"
    )
    issue_date: Optional[str] = Field(None, description="Issue date (YYYY-MM-DD)")
    
    # Issuing Authority
    issuing_authority: Optional[str] = Field(None)
    authority_officer: Optional[str] = Field(None)
    
    # Project Reference
    project_name: Optional[str] = Field(None)
    rera_registration_number: Optional[str] = Field(None)
    original_sanction_number: Optional[str] = Field(None)
    original_sanction_date: Optional[str] = Field(None)
    
    # Location
    plot_number: Optional[str] = Field(None)
    address: Optional[str] = Field(None)
    village: Optional[str] = Field(None)
    district: Optional[str] = Field(None)
    
    # Completion Details
    completion_percentage: Optional[float] = Field(
        None, 
        description="Completion percentage (0-100)"
    )
    completion_date: Optional[str] = Field(None, description="Date of completion")
    
    # Building Details
    buildings_completed: Optional[int] = Field(None)
    total_buildings: Optional[int] = Field(None)
    floors_completed: Optional[int] = Field(None)
    units_completed: Optional[int] = Field(None)
    total_units: Optional[int] = Field(None)
    
    # Area Details
    total_built_up_area: Optional[str] = Field(None)
    completed_area: Optional[str] = Field(None)
    
    # Compliance
    fire_safety_approved: bool = Field(default=False)
    structural_stability_certified: bool = Field(default=False)
    utilities_connected: bool = Field(default=False)
    
    # Pending Works (for partial completion)
    pending_works: List[str] = Field(
        default_factory=list,
        description="List of pending works"
    )
    
    # Occupancy Permission
    occupancy_allowed: bool = Field(default=False)
    max_occupancy: Optional[int] = Field(None)
    
    def validate_extraction(self) -> bool:
        """Validate completion certificate extraction"""
        errors = []
        
        if not self.certificate_number:
            errors.append("Missing certificate number")
        
        if not self.issuing_authority:
            errors.append("Missing issuing authority")
        
        self.validation_errors = errors
        self.is_valid = len(errors) == 0
        return self.is_valid
