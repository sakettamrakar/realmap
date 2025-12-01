"""
Analytics API Routes (Point 13).

Price trends and market analytics endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from cg_rera_extractor.api.deps import get_db
from cg_rera_extractor.api.schemas_api import (
    PriceTrendResponse,
    TimeframeEnum,
    GranularityEnum,
    EntityTypeEnum,
)
from cg_rera_extractor.api.services.analytics import fetch_price_trends

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/price-trends", response_model=PriceTrendResponse)
def get_price_trends(
    *,
    entity_id: int = Query(..., description="Project, Locality, or District ID"),
    entity_type: EntityTypeEnum = Query(
        EntityTypeEnum.PROJECT,
        description="Type of entity: project, locality, district, developer"
    ),
    timeframe: TimeframeEnum = Query(
        TimeframeEnum.ONE_YEAR,
        description="Analysis timeframe: 1M, 3M, 6M, 1Y, 2Y, 5Y, ALL"
    ),
    granularity: GranularityEnum = Query(
        GranularityEnum.QUARTERLY,
        description="Data granularity: daily, weekly, monthly, quarterly, yearly"
    ),
    unit_type: str | None = Query(
        None,
        description="Filter by unit type (e.g., '2BHK', '3BHK')"
    ),
    area_type: str | None = Query(
        None,
        description="Area type for price calculation: carpet, builtup, super_builtup"
    ),
    db=Depends(get_db),
):
    """
    Get price trend analytics for a project, locality, or district.
    
    Returns time-series data showing price movements over the specified timeframe.
    
    ## Parameters
    - **entity_id**: The ID of the entity to analyze
    - **entity_type**: Type of entity (project, locality, district, developer)
    - **timeframe**: How far back to look (1M to 5Y or ALL)
    - **granularity**: Time bucket size (daily to yearly)
    - **unit_type**: Optional filter for specific unit types
    - **area_type**: Which area measurement to use for price/sqft
    
    ## Response
    Returns a time series with:
    - Period labels (e.g., "Q1-2024")
    - Average, min, max, median prices per sqft
    - Period-over-period change percentages
    - Transaction volumes (when available)
    
    ## Example
    ```
    GET /analytics/price-trends?entity_id=123&timeframe=1Y&granularity=quarterly
    ```
    """
    # Currently only PROJECT entity type is supported
    if entity_type != EntityTypeEnum.PROJECT:
        raise HTTPException(
            status_code=400,
            detail=f"Entity type '{entity_type.value}' not yet supported. "
                   f"Currently only 'project' is implemented."
        )
    
    result = fetch_price_trends(
        db=db,
        entity_id=entity_id,
        entity_type=entity_type,
        timeframe=timeframe,
        granularity=granularity,
        unit_type=unit_type,
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Entity {entity_id} not found or no pricing data available"
        )
    
    return result


@router.get("/price-trends/compare")
def compare_price_trends(
    *,
    entity_ids: str = Query(
        ...,
        description="Comma-separated list of entity IDs to compare"
    ),
    entity_type: EntityTypeEnum = Query(EntityTypeEnum.PROJECT),
    timeframe: TimeframeEnum = Query(TimeframeEnum.ONE_YEAR),
    granularity: GranularityEnum = Query(GranularityEnum.QUARTERLY),
    db=Depends(get_db),
):
    """
    Compare price trends across multiple entities.
    
    Useful for comparing projects in the same locality or different localities.
    
    ## Parameters
    - **entity_ids**: Comma-separated list of IDs (e.g., "123,456,789")
    - Other parameters same as /price-trends
    
    ## Response
    Returns an array of PriceTrendResponse objects, one per entity.
    """
    try:
        ids = [int(id.strip()) for id in entity_ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid entity_ids format. Use comma-separated integers."
        )
    
    if len(ids) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 entities can be compared at once."
        )
    
    results = []
    for entity_id in ids:
        result = fetch_price_trends(
            db=db,
            entity_id=entity_id,
            entity_type=entity_type,
            timeframe=timeframe,
            granularity=granularity,
        )
        if result:
            results.append(result)
    
    if not results:
        raise HTTPException(
            status_code=404,
            detail="No pricing data found for any of the specified entities"
        )
    
    return {
        "comparisons": results,
        "entity_count": len(results),
    }


__all__ = ["router"]
