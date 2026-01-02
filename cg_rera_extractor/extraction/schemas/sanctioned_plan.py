"""
Sanctioned Plan Schema

Schema for data extracted from Government Sanctioned/Approved Plans.
"""

from typing import Optional, List, Dict
from pydantic import Field

from .base import BaseExtractionSchema


class SanctionedPlanSchema(BaseExtractionSchema):
    """
    Schema for Sanctioned/Approved Plan extraction.
    
    Government-approved development plans that authorize
    construction and development activities.
    """
    
    document_type: str = Field(default="sanctioned_plan")
    
    # Sanction Details
    sanction_number: Optional[str] = Field(None, description="Sanction/Approval number")
    sanction_date: Optional[str] = Field(None, description="Sanction date (YYYY-MM-DD)")
    valid_till: Optional[str] = Field(None, description="Validity end date")
    
    # Sanctioning Authority
    sanctioning_authority: Optional[str] = Field(
        None, 
        description="Authority name (e.g., RDA, Nagar Palika)"
    )
    authority_address: Optional[str] = Field(None)
    authority_officer: Optional[str] = Field(None, description="Approving officer name")
    
    # Project Details
    project_name: Optional[str] = Field(None)
    applicant_name: Optional[str] = Field(None, description="Applicant/Developer name")
    
    # Location
    plot_number: Optional[str] = Field(None)
    survey_numbers: List[str] = Field(default_factory=list)
    village: Optional[str] = Field(None)
    tehsil: Optional[str] = Field(None)
    district: Optional[str] = Field(None)
    
    # Area Details
    total_site_area: Optional[str] = Field(None, description="Total site area")
    proposed_built_up_area: Optional[str] = Field(None, description="Proposed built-up area")
    ground_coverage: Optional[str] = Field(None, description="Ground coverage %")
    far_fsi: Optional[str] = Field(None, description="FAR/FSI value")
    
    # Setbacks
    front_setback: Optional[str] = Field(None)
    rear_setback: Optional[str] = Field(None)
    side_setbacks: Optional[str] = Field(None)
    
    # Building Details
    number_of_buildings: Optional[int] = Field(None)
    number_of_floors: Optional[int] = Field(None, description="Maximum floors approved")
    building_height: Optional[str] = Field(None, description="Maximum height")
    basement_floors: Optional[int] = Field(None)
    
    # Unit Details
    total_units: Optional[int] = Field(None)
    residential_units: Optional[int] = Field(None)
    commercial_units: Optional[int] = Field(None)
    parking_spaces: Optional[int] = Field(None)
    
    # Land Use
    land_use_zone: Optional[str] = Field(None, description="Zoning classification")
    development_type: Optional[str] = Field(
        None, 
        description="Residential/Commercial/Industrial/Mixed"
    )
    
    # Conditions
    conditions: List[str] = Field(
        default_factory=list,
        description="Conditions attached to approval"
    )
    
    # Fee Details
    sanction_fee_paid: Optional[str] = Field(None)
    
    def validate_extraction(self) -> bool:
        """Validate sanctioned plan extraction"""
        errors = []
        
        if not self.sanction_number:
            errors.append("Missing sanction number")
        
        if not self.sanctioning_authority:
            errors.append("Missing sanctioning authority")
        
        self.validation_errors = errors
        self.is_valid = len(errors) == 0
        return self.is_valid
