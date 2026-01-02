"""
Building Plan Schema

Schema for data extracted from Building Floor Plans and Elevations.
"""

from typing import Optional, List, Dict
from pydantic import Field

from .base import BaseExtractionSchema


class FloorInfo(BaseExtractionSchema):
    """Information about a single floor"""
    floor_name: str = Field(..., description="Floor name (Ground/First/Second/etc.)")
    floor_number: Optional[int] = Field(None)
    floor_area: Optional[str] = Field(None, description="Floor area")
    units_on_floor: Optional[int] = Field(None)
    unit_types: List[str] = Field(default_factory=list, description="Types of units on floor")


class BuildingPlanSchema(BaseExtractionSchema):
    """
    Schema for Building Plan extraction.
    
    Includes floor plans, elevations, and structural details.
    """
    
    document_type: str = Field(default="building_plan")
    
    # Building Identification
    building_name: Optional[str] = Field(None)
    building_number: Optional[str] = Field(None)
    project_name: Optional[str] = Field(None)
    
    # Plan Type
    plan_type: Optional[str] = Field(
        None, 
        description="Type: Floor Plan/Elevation/Section/Site Plan"
    )
    
    # Overall Dimensions
    total_floors: Optional[int] = Field(None, description="Total number of floors")
    basement_floors: Optional[int] = Field(None)
    total_height: Optional[str] = Field(None, description="Building height")
    plinth_level: Optional[str] = Field(None)
    
    # Area Details
    total_built_up_area: Optional[str] = Field(None)
    carpet_area: Optional[str] = Field(None)
    super_built_up_area: Optional[str] = Field(None)
    common_area: Optional[str] = Field(None)
    
    # Floor Details
    floors: List[Dict] = Field(
        default_factory=list,
        description="Details of each floor"
    )
    
    # Unit Details
    total_units: Optional[int] = Field(None)
    unit_types: List[str] = Field(
        default_factory=list,
        description="Types: 1BHK, 2BHK, 3BHK, Shop, Office"
    )
    typical_unit_sizes: Dict[str, str] = Field(
        default_factory=dict,
        description="Size for each unit type"
    )
    
    # Setbacks
    front_setback: Optional[str] = Field(None)
    rear_setback: Optional[str] = Field(None)
    left_setback: Optional[str] = Field(None)
    right_setback: Optional[str] = Field(None)
    
    # Structural Details
    structure_type: Optional[str] = Field(
        None, 
        description="RCC/Load Bearing/Steel Frame"
    )
    foundation_type: Optional[str] = Field(None)
    
    # Parking
    parking_floors: Optional[int] = Field(None)
    parking_spaces: Optional[int] = Field(None)
    parking_type: Optional[str] = Field(None, description="Covered/Open/Basement")
    
    # Common Areas
    lift_count: Optional[int] = Field(None)
    staircase_count: Optional[int] = Field(None)
    
    # Amenities
    amenities: List[str] = Field(default_factory=list)
    
    def validate_extraction(self) -> bool:
        """Validate building plan extraction"""
        errors = []
        
        if not self.total_floors and not self.floors:
            errors.append("Missing floor information")
        
        self.validation_errors = errors
        self.is_valid = len(errors) == 0
        return self.is_valid
