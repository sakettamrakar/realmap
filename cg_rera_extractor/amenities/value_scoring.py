"""Value-for-money scoring helpers.

This module provides functions to compute a "value score" that combines
project quality (overall_score) with price information to help users
identify projects that offer good value relative to their price.

The v1 formula is intentionally simple:
- Higher overall_score → higher value
- Lower price (relative to median) → higher value
- The result is normalized to 0-100 scale
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from cg_rera_extractor.db.models import ProjectPricingSnapshot


# Default median price for CG region (in INR) - can be updated via config
# This is a reasonable estimate based on typical project prices
DEFAULT_MEDIAN_PRICE = 5_000_000  # 50 Lakhs

# Price range for normalization (min and max expected prices)
PRICE_FLOOR = 1_000_000    # 10 Lakhs
PRICE_CEILING = 50_000_000  # 5 Crores


def _to_float(value: Decimal | float | int | None) -> float | None:
    """Safely convert a numeric value to float."""
    if value is None:
        return None
    return float(value)


def compute_global_median_price(session: Session) -> float | None:
    """Compute the median price across all projects with pricing data.
    
    Returns the median of min_price_total from active pricing snapshots.
    Returns None if no pricing data is available.
    """
    # Get all active min_price_total values
    result = (
        session.query(ProjectPricingSnapshot.min_price_total)
        .filter(
            ProjectPricingSnapshot.is_active == True,
            ProjectPricingSnapshot.min_price_total.isnot(None),
        )
        .all()
    )
    
    prices = [float(r[0]) for r in result if r[0] is not None]
    
    if not prices:
        return None
    
    # Calculate median
    prices.sort()
    n = len(prices)
    if n % 2 == 0:
        return (prices[n // 2 - 1] + prices[n // 2]) / 2
    return prices[n // 2]


def compute_value_score(
    overall_score: float | None,
    price_min_total: float | None,
    price_max_total: float | None = None,
    context: dict[str, Any] | None = None,
) -> float | None:
    """Compute a value-for-money score combining quality and price.
    
    The v1 formula:
    1. Normalize overall_score to 0-1 (assuming it's on 0-100 scale)
    2. Normalize price to 0-1 using median as reference:
       - price_ratio = price / median_price
       - price_factor = 1 - min(price_ratio, 2) / 2
       - This gives 1.0 for free, 0.5 for median price, 0 for 2x median
    3. Value score = weighted combination:
       - 60% quality (overall_score)
       - 40% price factor
    4. Scale to 0-100
    
    Args:
        overall_score: Project quality score (0-100 scale)
        price_min_total: Minimum total price for the project
        price_max_total: Maximum total price (optional, uses min if not provided)
        context: Optional dict with 'median_price' to override default
    
    Returns:
        Value score on 0-100 scale, or None if required inputs are missing
    """
    # Require both score and price
    if overall_score is None or price_min_total is None:
        return None
    
    # Get median price from context or use default
    median_price = DEFAULT_MEDIAN_PRICE
    if context and "median_price" in context:
        median_price = context["median_price"]
    
    # Ensure median is positive
    if median_price <= 0:
        median_price = DEFAULT_MEDIAN_PRICE
    
    # Use the lower price bound for value calculation
    # (being conservative - if min price is low, that's the value proposition)
    price = price_min_total
    
    # Normalize overall_score to 0-1 (assuming 0-100 scale)
    score_normalized = max(0, min(100, overall_score)) / 100.0
    
    # Calculate price factor
    # price_ratio: how expensive is this relative to median?
    # A price equal to median gives ratio = 1.0
    # A price double the median gives ratio = 2.0
    price_ratio = price / median_price
    
    # Convert to a "value" factor where lower price = higher factor
    # Cap at 2x median (very expensive) and floor at 0 (free)
    # Formula: 1 - (capped_ratio / 2)
    # This gives:
    #   - Free (ratio=0): factor = 1.0 (best value)
    #   - At median (ratio=1): factor = 0.5 (neutral)
    #   - At 2x median (ratio=2): factor = 0.0 (poor value)
    capped_ratio = max(0, min(price_ratio, 2.0))
    price_factor = 1.0 - (capped_ratio / 2.0)
    
    # Weighted combination
    # Quality matters more (60%) than just being cheap (40%)
    QUALITY_WEIGHT = 0.60
    PRICE_WEIGHT = 0.40
    
    value_normalized = (
        QUALITY_WEIGHT * score_normalized +
        PRICE_WEIGHT * price_factor
    )
    
    # Scale to 0-100 and round
    value_score = round(value_normalized * 100, 2)
    
    return value_score


def get_value_bucket(value_score: float | None) -> str:
    """Convert value score to a human-readable bucket.
    
    Args:
        value_score: The computed value score (0-100)
    
    Returns:
        One of: "excellent", "good", "fair", "poor", or "unknown"
    """
    if value_score is None:
        return "unknown"
    
    if value_score >= 70:
        return "excellent"
    elif value_score >= 55:
        return "good"
    elif value_score >= 40:
        return "fair"
    else:
        return "poor"


__all__ = [
    "compute_value_score",
    "compute_global_median_price",
    "get_value_bucket",
    "DEFAULT_MEDIAN_PRICE",
]
