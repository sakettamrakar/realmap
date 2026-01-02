"""
Price Trends Analytics Service (Point 13).

Aggregates historical pricing data into time-series for analytics.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from cg_rera_extractor.db import Project, ProjectPricingSnapshot
from cg_rera_extractor.api.schemas_api import (
    PriceTrendDataPoint,
    PriceTrendResponse,
    TimeframeEnum,
    GranularityEnum,
    EntityTypeEnum,
    DataProvenance,
    ExtractionMethodEnum,
)


def _get_timeframe_start(timeframe: TimeframeEnum, reference_date: date | None = None) -> date:
    """Calculate the start date based on timeframe."""
    ref = reference_date or date.today()
    
    mapping = {
        TimeframeEnum.ONE_MONTH: timedelta(days=30),
        TimeframeEnum.THREE_MONTHS: timedelta(days=90),
        TimeframeEnum.SIX_MONTHS: timedelta(days=180),
        TimeframeEnum.ONE_YEAR: timedelta(days=365),
        TimeframeEnum.TWO_YEARS: timedelta(days=730),
        TimeframeEnum.FIVE_YEARS: timedelta(days=1825),
        TimeframeEnum.ALL: timedelta(days=3650),  # 10 years max
    }
    
    return ref - mapping.get(timeframe, timedelta(days=365))


def _get_period_label(period_start: date, granularity: GranularityEnum) -> str:
    """Generate a human-readable period label."""
    if granularity == GranularityEnum.DAILY:
        return period_start.strftime("%Y-%m-%d")
    elif granularity == GranularityEnum.WEEKLY:
        return f"W{period_start.isocalendar()[1]}-{period_start.year}"
    elif granularity == GranularityEnum.MONTHLY:
        return period_start.strftime("%b %Y")
    elif granularity == GranularityEnum.QUARTERLY:
        quarter = (period_start.month - 1) // 3 + 1
        return f"Q{quarter}-{period_start.year}"
    elif granularity == GranularityEnum.YEARLY:
        return str(period_start.year)
    return period_start.isoformat()


def _get_period_bounds(period_start: date, granularity: GranularityEnum) -> tuple[date, date]:
    """Get the start and end dates for a period."""
    if granularity == GranularityEnum.DAILY:
        return period_start, period_start
    elif granularity == GranularityEnum.WEEKLY:
        # Week starts on Monday
        week_start = period_start - timedelta(days=period_start.weekday())
        week_end = week_start + timedelta(days=6)
        return week_start, week_end
    elif granularity == GranularityEnum.MONTHLY:
        month_start = period_start.replace(day=1)
        if month_start.month == 12:
            month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
        return month_start, month_end
    elif granularity == GranularityEnum.QUARTERLY:
        quarter = (period_start.month - 1) // 3
        quarter_start = date(period_start.year, quarter * 3 + 1, 1)
        if quarter == 3:
            quarter_end = date(period_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            quarter_end = date(period_start.year, (quarter + 1) * 3 + 1, 1) - timedelta(days=1)
        return quarter_start, quarter_end
    elif granularity == GranularityEnum.YEARLY:
        year_start = date(period_start.year, 1, 1)
        year_end = date(period_start.year, 12, 31)
        return year_start, year_end
    
    return period_start, period_start


def _aggregate_snapshots_for_period(
    snapshots: list[ProjectPricingSnapshot],
    period_start: date,
    period_end: date,
) -> dict[str, Any] | None:
    """Aggregate pricing snapshots within a period."""
    period_snapshots = [
        s for s in snapshots
        if s.snapshot_date and period_start <= s.snapshot_date <= period_end
    ]
    
    if not period_snapshots:
        return None
    
    # Collect price values
    prices_per_sqft = [
        float(s.min_price_per_sqft) for s in period_snapshots
        if s.min_price_per_sqft is not None
    ]
    prices_per_sqft.extend([
        float(s.max_price_per_sqft) for s in period_snapshots
        if s.max_price_per_sqft is not None
    ])
    
    total_prices = [
        float(s.min_price_total) for s in period_snapshots
        if s.min_price_total is not None
    ]
    total_prices.extend([
        float(s.max_price_total) for s in period_snapshots
        if s.max_price_total is not None
    ])
    
    if not prices_per_sqft and not total_prices:
        return None
    
    result: dict[str, Any] = {
        "sample_size": len(period_snapshots),
    }
    
    if prices_per_sqft:
        prices_per_sqft.sort()
        result["avg_price_per_sqft"] = sum(prices_per_sqft) / len(prices_per_sqft)
        result["min_price_per_sqft"] = min(prices_per_sqft)
        result["max_price_per_sqft"] = max(prices_per_sqft)
        mid = len(prices_per_sqft) // 2
        result["median_price_per_sqft"] = (
            prices_per_sqft[mid] if len(prices_per_sqft) % 2 == 1
            else (prices_per_sqft[mid - 1] + prices_per_sqft[mid]) / 2
        )
    
    if total_prices:
        result["avg_total_price"] = sum(total_prices) / len(total_prices)
        result["min_total_price"] = min(total_prices)
        result["max_total_price"] = max(total_prices)
    
    return result


def fetch_price_trends(
    db: Session,
    entity_id: int,
    entity_type: EntityTypeEnum = EntityTypeEnum.PROJECT,
    timeframe: TimeframeEnum = TimeframeEnum.ONE_YEAR,
    granularity: GranularityEnum = GranularityEnum.QUARTERLY,
    unit_type: str | None = None,
) -> PriceTrendResponse | None:
    """
    Fetch price trend data for a project, locality, or district.
    
    Aggregates historical pricing snapshots into time-series data points.
    """
    # For now, only PROJECT entity type is implemented
    if entity_type != EntityTypeEnum.PROJECT:
        # TODO: Implement locality/district aggregation
        return None
    
    # Fetch the project
    project = db.query(Project).filter(Project.id == entity_id).first()
    if not project:
        return None
    
    # Determine project IDs to include (all registrations for the same parent)
    project_ids = [entity_id]
    if project.parent_project_id:
        related_ids = (
            db.query(Project.id)
            .filter(Project.parent_project_id == project.parent_project_id)
            .all()
        )
        project_ids = [r[0] for r in related_ids]

    # Determine date range
    start_date = _get_timeframe_start(timeframe)
    end_date = date.today()
    
    # Fetch all pricing snapshots in range
    query = (
        db.query(ProjectPricingSnapshot)
        .filter(
            ProjectPricingSnapshot.project_id.in_(project_ids),
            ProjectPricingSnapshot.is_active == True,
            ProjectPricingSnapshot.snapshot_date >= start_date,
            ProjectPricingSnapshot.snapshot_date <= end_date,
        )
    )
    
    if unit_type:
        query = query.filter(ProjectPricingSnapshot.unit_type_label == unit_type)
    
    snapshots = query.order_by(ProjectPricingSnapshot.snapshot_date).all()
    
    if not snapshots:
        # Return empty response with metadata
        return PriceTrendResponse(
            entity_id=entity_id,
            entity_type=entity_type,
            entity_name=project.project_name,
            timeframe=timeframe,
            granularity=granularity,
            trend_data=[],
            data_points_count=0,
            provenance=DataProvenance(
                last_updated_at=project.scraped_at,
                source_domain="rera.cg.gov.in",
                extraction_method=ExtractionMethodEnum.SCRAPER,
                data_quality_score=project.data_quality_score,
            ),
        )
    
    # Group snapshots into periods
    trend_data: list[PriceTrendDataPoint] = []
    previous_avg: float | None = None
    
    # Generate periods
    current_date = start_date
    while current_date <= end_date:
        period_start, period_end = _get_period_bounds(current_date, granularity)
        
        # Ensure we don't go past end_date
        if period_start > end_date:
            break
        
        aggregated = _aggregate_snapshots_for_period(snapshots, period_start, period_end)
        
        if aggregated:
            current_avg = aggregated.get("avg_price_per_sqft")
            
            # Calculate change from previous period
            change_pct = None
            change_abs = None
            if previous_avg and current_avg:
                change_abs = current_avg - previous_avg
                change_pct = (change_abs / previous_avg) * 100
            
            data_point = PriceTrendDataPoint(
                period=_get_period_label(period_start, granularity),
                period_start=period_start,
                period_end=period_end,
                avg_price_per_sqft=aggregated.get("avg_price_per_sqft"),
                min_price_per_sqft=aggregated.get("min_price_per_sqft"),
                max_price_per_sqft=aggregated.get("max_price_per_sqft"),
                median_price_per_sqft=aggregated.get("median_price_per_sqft"),
                avg_total_price=aggregated.get("avg_total_price"),
                min_total_price=aggregated.get("min_total_price"),
                max_total_price=aggregated.get("max_total_price"),
                sample_size=aggregated.get("sample_size"),
                change_pct=round(change_pct, 2) if change_pct else None,
                change_abs=round(change_abs, 2) if change_abs else None,
                confidence_level="high" if aggregated.get("sample_size", 0) >= 3 else "low",
            )
            trend_data.append(data_point)
            previous_avg = current_avg
        
        # Move to next period
        if granularity == GranularityEnum.DAILY:
            current_date += timedelta(days=1)
        elif granularity == GranularityEnum.WEEKLY:
            current_date += timedelta(weeks=1)
        elif granularity == GranularityEnum.MONTHLY:
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
        elif granularity == GranularityEnum.QUARTERLY:
            month = current_date.month + 3
            year = current_date.year
            if month > 12:
                month -= 12
                year += 1
            current_date = date(year, month, 1)
        elif granularity == GranularityEnum.YEARLY:
            current_date = date(current_date.year + 1, 1, 1)
    
    # Calculate summary statistics
    all_avgs = [dp.avg_price_per_sqft for dp in trend_data if dp.avg_price_per_sqft]
    current_avg_price = all_avgs[-1] if all_avgs else None
    period_high = max(all_avgs) if all_avgs else None
    period_low = min(all_avgs) if all_avgs else None
    
    overall_change = None
    if len(all_avgs) >= 2:
        overall_change = round(((all_avgs[-1] - all_avgs[0]) / all_avgs[0]) * 100, 2)
    
    earliest = trend_data[0].period_start if trend_data else None
    latest = trend_data[-1].period_end if trend_data else None
    
    return PriceTrendResponse(
        entity_id=entity_id,
        entity_type=entity_type,
        entity_name=project.project_name,
        timeframe=timeframe,
        granularity=granularity,
        trend_data=trend_data,
        current_avg_price=current_avg_price,
        period_high=period_high,
        period_low=period_low,
        overall_change_pct=overall_change,
        data_points_count=len(trend_data),
        earliest_date=earliest,
        latest_date=latest,
        provenance=DataProvenance(
            last_updated_at=project.scraped_at,
            source_domain="rera.cg.gov.in",
            extraction_method=ExtractionMethodEnum.SCRAPER,
            data_quality_score=project.data_quality_score,
        ),
    )


__all__ = ["fetch_price_trends"]
