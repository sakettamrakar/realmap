"""
Data normalization utilities for the RealMap ETL pipeline.

Provides functions for:
- Area unit conversion (sqft, sqm, acres, hectares, yards)
- Price normalization (handling lakhs, crores, rupee symbols)
- Category normalization (project types, statuses)
- Text normalization (casing, whitespace, special characters)

Created: 2024-12-10 (Data Audit implementation)
"""
from __future__ import annotations

import re
from decimal import Decimal


# =============================================================================
# Area Conversion Constants
# =============================================================================

# Conversion factors to square meters (base unit)
SQFT_TO_SQM = Decimal("0.092903")
SQYD_TO_SQM = Decimal("0.836127")
ACRE_TO_SQM = Decimal("4046.8564224")
HECTARE_TO_SQM = Decimal("10000")
BIGHA_TO_SQM = Decimal("2529.28")  # Approximate, varies by state

# Conversion factors to square feet (common unit)
SQM_TO_SQFT = Decimal("10.7639")
SQYD_TO_SQFT = Decimal("9")
ACRE_TO_SQFT = Decimal("43560")
HECTARE_TO_SQFT = Decimal("107639.104")


# =============================================================================
# Area Normalization
# =============================================================================

def normalize_area_to_sqm(value: str | float | Decimal | None, unit: str = "sqft") -> Decimal | None:
    """
    Convert area value to square meters.
    
    Args:
        value: The area value (can be string with unit suffix)
        unit: Default unit if not specified in value ('sqft', 'sqm', 'sqyd', 'acre', 'ha', 'bigha')
    
    Returns:
        Area in square meters, or None if conversion fails
    """
    if value is None:
        return None
    
    # Handle string input with potential unit suffix
    if isinstance(value, str):
        value = value.strip().replace(",", "")
        
        # Detect unit from string
        unit_patterns = {
            'sqm': r'(sq\.?m|sqm|m²|square\s*meters?)',
            'sqft': r'(sq\.?ft|sqft|ft²|sft|square\s*feet)',
            'sqyd': r'(sq\.?yd|sqyd|yd²|square\s*yards?|gaj)',
            'acre': r'(acres?)',
            'hectare': r'(ha|hectares?)',
            'bigha': r'(bighas?)',
        }
        
        for detected_unit, pattern in unit_patterns.items():
            if re.search(pattern, value, re.IGNORECASE):
                unit = detected_unit
                value = re.sub(pattern, '', value, flags=re.IGNORECASE).strip()
                break
        
        # Extract numeric value
        match = re.search(r'[\d,.]+', value)
        if not match:
            return None
        value = match.group(0).replace(",", "")
    
    try:
        area_value = Decimal(str(value))
    except (ValueError, ArithmeticError):
        return None
    
    # Convert to square meters
    conversion_factors = {
        'sqm': Decimal("1"),
        'sqft': SQFT_TO_SQM,
        'sqyd': SQYD_TO_SQM,
        'acre': ACRE_TO_SQM,
        'hectare': HECTARE_TO_SQM,
        'ha': HECTARE_TO_SQM,
        'bigha': BIGHA_TO_SQM,
    }
    
    factor = conversion_factors.get(unit.lower(), SQFT_TO_SQM)
    return area_value * factor


def normalize_area_to_sqft(value: str | float | Decimal | None, unit: str = "sqm") -> Decimal | None:
    """
    Convert area value to square feet.
    
    Args:
        value: The area value (can be string with unit suffix)
        unit: Default unit if not specified in value
    
    Returns:
        Area in square feet, or None if conversion fails
    """
    sqm_value = normalize_area_to_sqm(value, unit)
    if sqm_value is None:
        return None
    return sqm_value * SQM_TO_SQFT


def sqm_to_sqft(sqm: Decimal | float | None) -> Decimal | None:
    """Direct conversion from square meters to square feet."""
    if sqm is None:
        return None
    return Decimal(str(sqm)) * SQM_TO_SQFT


def sqft_to_sqm(sqft: Decimal | float | None) -> Decimal | None:
    """Direct conversion from square feet to square meters."""
    if sqft is None:
        return None
    return Decimal(str(sqft)) * SQFT_TO_SQM


# =============================================================================
# Price Normalization
# =============================================================================

def normalize_price(value: str | float | int | None) -> Decimal | None:
    """
    Normalize Indian price strings to numeric value in INR.
    
    Handles:
    - ₹1,00,000 -> 100000
    - 1 Cr / 1 Crore -> 10000000
    - 50 L / 50 Lac / 50 Lakh -> 5000000
    - 1.5 Cr -> 15000000
    - Rs. 1,00,000 -> 100000
    
    Args:
        value: Price string or numeric value
    
    Returns:
        Price in INR as Decimal, or None if parsing fails
    """
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    
    if isinstance(value, Decimal):
        return value
    
    # Clean the string
    value = str(value).strip()
    # Remove currency symbols and prefixes
    value = value.replace('₹', '').replace('$', '')
    value = re.sub(r'Rs\.?\s*', '', value, flags=re.IGNORECASE)
    value = value.replace(",", "")
    
    # Handle crores and lakhs
    multiplier = Decimal("1")
    
    if re.search(r'cr(?:ore)?s?', value, re.IGNORECASE):
        multiplier = Decimal("10000000")  # 1 Crore = 10^7
        value = re.sub(r'cr(?:ore)?s?', '', value, flags=re.IGNORECASE)
    elif re.search(r'l(?:ac|akh)?s?', value, re.IGNORECASE):
        multiplier = Decimal("100000")  # 1 Lakh = 10^5
        value = re.sub(r'l(?:ac|akh)?s?', '', value, flags=re.IGNORECASE)
    elif re.search(r'k', value, re.IGNORECASE):
        multiplier = Decimal("1000")
        value = re.sub(r'k', '', value, flags=re.IGNORECASE)
    
    # Extract numeric value
    value = value.strip()
    if not value:
        return None
    
    try:
        numeric_value = Decimal(value)
        return numeric_value * multiplier
    except (ValueError, ArithmeticError):
        return None


def price_per_sqft(total_price: Decimal | None, area_sqft: Decimal | None) -> Decimal | None:
    """Calculate price per square foot."""
    if total_price is None or area_sqft is None or area_sqft == 0:
        return None
    return total_price / area_sqft


def format_price_lakhs(price_inr: Decimal | None) -> str | None:
    """Format price in lakhs for display (e.g., 50.5L)."""
    if price_inr is None:
        return None
    lakhs = price_inr / Decimal("100000")
    if lakhs >= 100:
        crores = lakhs / 100
        return f"{crores:.2f} Cr"
    return f"{lakhs:.2f} L"


# =============================================================================
# Category Normalization
# =============================================================================

PROJECT_STATUS_MAP = {
    'ongoing': 'ongoing',
    'under construction': 'ongoing',
    'in progress': 'ongoing',
    'launched': 'ongoing',
    'new launch': 'ongoing',
    'completed': 'completed',
    'ready to move': 'completed',
    'possession': 'completed',
    'delivered': 'completed',
    'ready': 'completed',
    'approved': 'approved',
    'registered': 'approved',
    'expired': 'expired',
    'lapsed': 'expired',
    'revoked': 'revoked',
    'cancelled': 'cancelled',
}

PROJECT_TYPE_MAP = {
    'residential': 'residential',
    'residential project': 'residential',
    'group housing': 'residential',
    'apartment': 'residential',
    'flats': 'residential',
    'commercial': 'commercial',
    'commercial project': 'commercial',
    'shop': 'commercial',
    'office': 'commercial',
    'mixed': 'mixed',
    'mixed use': 'mixed',
    'plotted': 'plotted',
    'plotted development': 'plotted',
    'villa': 'villa',
    'villas': 'villa',
    'township': 'township',
    'integrated township': 'township',
}


def normalize_project_status(status: str | None) -> str | None:
    """Normalize project status to standard values."""
    if not status:
        return None
    status_lower = status.strip().lower()
    return PROJECT_STATUS_MAP.get(status_lower, status)


def normalize_project_type(project_type: str | None) -> str | None:
    """Normalize project type to standard values."""
    if not project_type:
        return None
    type_lower = project_type.strip().lower()
    return PROJECT_TYPE_MAP.get(type_lower, project_type)


# =============================================================================
# Text Normalization
# =============================================================================

def normalize_whitespace(text: str | None) -> str | None:
    """Collapse multiple whitespace chars to single space."""
    if not text:
        return None
    return " ".join(text.split())


def normalize_name(name: str | None) -> str | None:
    """Normalize a name/title to title case with cleaned whitespace."""
    if not name:
        return None
    text = normalize_whitespace(name)
    if text:
        return text.title()
    return None


def remove_special_chars(text: str | None, keep_chars: str = "") -> str | None:
    """Remove special characters from text, optionally keeping specified chars."""
    if not text:
        return None
    pattern = f"[^a-zA-Z0-9\\s{re.escape(keep_chars)}]"
    return re.sub(pattern, "", text)


def extract_numeric(text: str | None) -> str | None:
    """Extract only numeric characters from text."""
    if not text:
        return None
    return re.sub(r"[^0-9]", "", text)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Area conversion
    "normalize_area_to_sqm",
    "normalize_area_to_sqft",
    "sqm_to_sqft",
    "sqft_to_sqm",
    # Price conversion
    "normalize_price",
    "price_per_sqft",
    "format_price_lakhs",
    # Category normalization
    "normalize_project_status",
    "normalize_project_type",
    # Text normalization
    "normalize_whitespace",
    "normalize_name",
    "remove_special_chars",
    "extract_numeric",
    # Constants
    "SQFT_TO_SQM",
    "SQM_TO_SQFT",
    "ACRE_TO_SQM",
    "HECTARE_TO_SQM",
]
