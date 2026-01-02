"""
Registration Certificate Schema

Schema for data extracted from RERA Registration Certificates.
"""

from datetime import date
from typing import Optional, List, Dict
from pydantic import Field, validator
import re

from .base import BaseExtractionSchema


class RegistrationCertificateSchema(BaseExtractionSchema):
    """
    Schema for RERA Registration Certificate extraction.
    
    A Registration Certificate contains:
    - Registration number and dates
    - Project information
    - Promoter details
    - Authority information
    """
    
    document_type: str = Field(default="registration_certificate")
    
    # Registration Details
    registration_number: Optional[str] = Field(
        None, 
        description="RERA registration number (e.g., PCGRERA010618000020)"
    )
    registration_date: Optional[str] = Field(
        None, 
        description="Date of registration (YYYY-MM-DD)"
    )
    valid_from: Optional[str] = Field(
        None, 
        description="Validity start date (YYYY-MM-DD)"
    )
    valid_till: Optional[str] = Field(
        None, 
        description="Validity end date (YYYY-MM-DD)"
    )
    
    # Project Details
    project_name: Optional[str] = Field(
        None, 
        description="Official project name"
    )
    project_type: Optional[str] = Field(
        None, 
        description="Type: Residential/Commercial/Plotted Development/Mixed"
    )
    project_address: Optional[str] = Field(
        None, 
        description="Complete project address"
    )
    project_district: Optional[str] = Field(
        None, 
        description="District name"
    )
    project_tehsil: Optional[str] = Field(
        None, 
        description="Tehsil/Taluka name"
    )
    project_state: Optional[str] = Field(
        default="Chhattisgarh",
        description="State name"
    )
    
    # Area Details
    total_land_area: Optional[str] = Field(
        None, 
        description="Total land area with unit (e.g., '5 Acres', '2000 Sq.M')"
    )
    total_built_up_area: Optional[str] = Field(
        None, 
        description="Total built-up area with unit"
    )
    total_units: Optional[int] = Field(
        None, 
        description="Total number of units/plots"
    )
    
    # Promoter Details
    promoter_name: Optional[str] = Field(
        None, 
        description="Name of the promoter/developer"
    )
    promoter_type: Optional[str] = Field(
        None, 
        description="Type: Individual/Company/Partnership/LLP/Society"
    )
    promoter_address: Optional[str] = Field(
        None, 
        description="Promoter's registered address"
    )
    
    # Authority Details
    issuing_authority: Optional[str] = Field(
        default="Chhattisgarh Real Estate Regulatory Authority",
        description="Name of issuing authority"
    )
    authority_seal_present: bool = Field(
        default=False,
        description="Whether authority seal/stamp is visible"
    )
    signature_present: bool = Field(
        default=False,
        description="Whether authorized signature is present"
    )
    
    # QR Code (if present)
    qr_code_data: Optional[str] = Field(
        None, 
        description="Data from QR code if present and readable"
    )
    
    @validator('registration_number')
    def validate_registration_number(cls, v):
        """Validate RERA registration number format"""
        if v:
            # CG RERA format: PCGRERA followed by digits
            pattern = r'^P?CG?RERA\d{6,12}$'
            v = v.upper().replace(' ', '').replace('-', '')
            if not re.match(pattern, v, re.IGNORECASE):
                # Try to extract valid number
                match = re.search(r'P?CG?RERA\d{6,12}', v, re.IGNORECASE)
                if match:
                    return match.group(0).upper()
        return v
    
    @validator('registration_date', 'valid_from', 'valid_till')
    def validate_date(cls, v):
        """Normalize date format to YYYY-MM-DD"""
        if v:
            # Try common date formats
            import re
            from datetime import datetime
            
            # Already in correct format
            if re.match(r'^\d{4}-\d{2}-\d{2}$', v):
                return v
            
            # DD-MM-YYYY or DD/MM/YYYY
            match = re.match(r'^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$', v)
            if match:
                day, month, year = match.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # Try parsing common formats
            formats = [
                "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d",
                "%d %b %Y", "%d %B %Y", "%B %d, %Y"
            ]
            for fmt in formats:
                try:
                    dt = datetime.strptime(v.strip(), fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
        return v
    
    @validator('project_type')
    def normalize_project_type(cls, v):
        """Normalize project type to standard values"""
        if v:
            v_lower = v.lower()
            if 'residential' in v_lower:
                return 'Residential'
            elif 'commercial' in v_lower:
                return 'Commercial'
            elif 'plot' in v_lower:
                return 'Plotted Development'
            elif 'mixed' in v_lower:
                return 'Mixed Use'
        return v
    
    def validate_extraction(self) -> bool:
        """Validate the extraction has minimum required fields"""
        errors = []
        
        # Must have registration number
        if not self.registration_number:
            errors.append("Missing registration number")
        
        # Should have at least one date
        if not any([self.registration_date, self.valid_from, self.valid_till]):
            errors.append("No dates found")
        
        # Should have project name or promoter name
        if not self.project_name and not self.promoter_name:
            errors.append("Missing both project and promoter name")
        
        self.validation_errors = errors
        self.is_valid = len(errors) == 0
        return self.is_valid
