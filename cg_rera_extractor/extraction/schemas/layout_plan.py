"""
Layout Plan Schema

Schema for data extracted from Site/Layout Plans.
"""

from typing import Optional, List, Dict
from pydantic import Field

from .base import BaseExtractionSchema


class PlotInfo(BaseExtractionSchema):
    """Individual plot information"""
    plot_number: str = Field(..., description="Plot number/ID")
    area: Optional[str] = Field(None, description="Plot area with unit")
    dimensions: Optional[str] = Field(None, description="Plot dimensions (e.g., '30x40 ft')")
    plot_type: Optional[str] = Field(None, description="Residential/Commercial/Green")
    facing: Optional[str] = Field(None, description="Direction facing (North/South/East/West)")


class LayoutPlanSchema(BaseExtractionSchema):
    """
    Schema for Layout/Site Plan extraction.
    
    A Layout Plan contains:
    - Overall land details
    - Plot division information
    - Road and infrastructure details
    - Open space and amenity information
    """
    
    document_type: str = Field(default="layout_plan")
    
    # Project Identification
    project_name: Optional[str] = Field(None, description="Project name")
    registration_number: Optional[str] = Field(None, description="RERA registration number")
    layout_number: Optional[str] = Field(None, description="Layout/sanction number")
    
    # Land Details
    total_land_area: Optional[str] = Field(None, description="Total land area with unit")
    total_saleable_area: Optional[str] = Field(None, description="Total saleable area")
    net_plot_area: Optional[str] = Field(None, description="Net plot area after roads")
    
    # Plot Summary
    total_plots: Optional[int] = Field(None, description="Total number of plots")
    residential_plots: Optional[int] = Field(None, description="Number of residential plots")
    commercial_plots: Optional[int] = Field(None, description="Number of commercial plots")
    
    # Plot Dimensions (common sizes)
    plot_sizes: List[str] = Field(
        default_factory=list,
        description="List of plot sizes (e.g., ['30x40', '30x50', '40x60'])"
    )
    
    # Road Details
    main_road_width: Optional[str] = Field(None, description="Main road width (e.g., '40 ft')")
    internal_road_widths: List[str] = Field(
        default_factory=list,
        description="Internal road widths"
    )
    road_area: Optional[str] = Field(None, description="Total road area")
    road_area_percentage: Optional[float] = Field(None, description="Road area as % of total")
    
    # Open Spaces
    open_space_area: Optional[str] = Field(None, description="Total open space area")
    open_space_percentage: Optional[float] = Field(None, description="Open space as % of total")
    park_area: Optional[str] = Field(None, description="Park/garden area")
    green_belt_area: Optional[str] = Field(None, description="Green belt area")
    
    # Amenities
    amenities: List[str] = Field(
        default_factory=list,
        description="List of amenities (Park, Community Hall, Temple, etc.)"
    )
    
    # Boundaries
    boundaries: Dict[str, str] = Field(
        default_factory=dict,
        description="Boundaries: {north, south, east, west}"
    )
    
    # Survey Details
    survey_numbers: List[str] = Field(
        default_factory=list,
        description="Land survey/khasra numbers"
    )
    village: Optional[str] = Field(None, description="Village name")
    tehsil: Optional[str] = Field(None, description="Tehsil name")
    district: Optional[str] = Field(None, description="District name")
    
    # Approval Details
    approval_authority: Optional[str] = Field(None, description="Approving authority name")
    approval_date: Optional[str] = Field(None, description="Approval date (YYYY-MM-DD)")
    approval_number: Optional[str] = Field(None, description="Approval/sanction number")
    
    # Individual Plots (if extractable)
    plots: List[Dict] = Field(
        default_factory=list,
        description="List of individual plot details"
    )
    
    def validate_extraction(self) -> bool:
        """Validate the extraction"""
        errors = []
        
        if not self.total_plots and not self.plots:
            errors.append("No plot information found")
        
        if not self.total_land_area:
            errors.append("Missing total land area")
        
        self.validation_errors = errors
        self.is_valid = len(errors) == 0
        return self.is_valid
