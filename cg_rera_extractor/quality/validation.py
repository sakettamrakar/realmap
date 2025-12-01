"""
Validation helpers for normalized V1 projects.

Point 27 Implementation: Automated QA Gates & Price Sanity Checks
- Price bounds checking (absolute min/max thresholds)
- Outlier detection (locality average comparison)
- Missing critical fields detection
- QA flags persistence structure
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from cg_rera_extractor.parsing.schema import V1Project


# =============================================================================
# POINT 27: QA Status & Flag Definitions
# =============================================================================


class QAStatus(str, Enum):
    """Overall QA validation status."""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    PENDING = "pending"


class QAFlagType(str, Enum):
    """Types of QA flags that can be raised."""
    PRICE_OUTLIER = "price_outlier"
    PRICE_BELOW_MIN = "price_below_min"
    PRICE_ABOVE_MAX = "price_above_max"
    PRICE_LOCALITY_MISMATCH = "price_locality_mismatch"
    MISSING_CRITICAL = "missing_critical"
    INVALID_FORMAT = "invalid_format"
    BOUNDS_EXCEEDED = "bounds_exceeded"
    DATA_INCONSISTENCY = "data_inconsistency"
    STALE_DATA = "stale_data"


@dataclass
class QAFlag:
    """Individual QA flag with metadata."""
    flag_type: QAFlagType
    severity: str  # "error", "warning", "info"
    message: str
    field_name: str | None = None
    expected_value: Any = None
    actual_value: Any = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "flag_type": self.flag_type.value,
            "severity": self.severity,
            "message": self.message,
            "field_name": self.field_name,
            "expected_value": str(self.expected_value) if self.expected_value else None,
            "actual_value": str(self.actual_value) if self.actual_value else None,
        }


@dataclass
class QAResult:
    """Complete QA validation result for a project."""
    status: QAStatus = QAStatus.PENDING
    flags: list[QAFlag] = field(default_factory=list)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    validator_version: str = "1.0.0"
    
    def add_flag(self, flag: QAFlag) -> None:
        self.flags.append(flag)
        # Update status based on severity
        if flag.severity == "error":
            self.status = QAStatus.FAILED
        elif flag.severity == "warning" and self.status != QAStatus.FAILED:
            self.status = QAStatus.WARNING
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "flags": [f.to_dict() for f in self.flags],
            "checked_at": self.checked_at.isoformat(),
            "validator_version": self.validator_version,
            "flag_count": len(self.flags),
            "error_count": sum(1 for f in self.flags if f.severity == "error"),
            "warning_count": sum(1 for f in self.flags if f.severity == "warning"),
        }
    
    @property
    def has_errors(self) -> bool:
        return any(f.severity == "error" for f in self.flags)
    
    @property
    def has_warnings(self) -> bool:
        return any(f.severity == "warning" for f in self.flags)


# =============================================================================
# POINT 27: Price Sanity Configuration
# =============================================================================


@dataclass
class PriceSanityConfig:
    """Configuration for price sanity checks."""
    # Absolute bounds (INR)
    min_price_total: Decimal = Decimal("100000")  # 1 Lakh minimum
    max_price_total: Decimal = Decimal("10000000000")  # 1000 Crore maximum
    
    # Per sqft bounds (INR)
    min_price_per_sqft: Decimal = Decimal("500")  # ₹500/sqft minimum
    max_price_per_sqft: Decimal = Decimal("100000")  # ₹1,00,000/sqft maximum
    
    # Locality comparison threshold
    locality_deviation_threshold: float = 0.30  # 30% deviation from locality avg
    
    # Area bounds (sqft)
    min_area_sqft: Decimal = Decimal("100")  # 100 sqft minimum
    max_area_sqft: Decimal = Decimal("100000")  # 1,00,000 sqft maximum


DEFAULT_PRICE_CONFIG = PriceSanityConfig()


# =============================================================================
# POINT 27: Critical Fields Definition
# =============================================================================


CRITICAL_FIELDS = [
    "rera_registration_number",
    "project_name",
    "district",
]

IMPORTANT_FIELDS = [
    "project_status",
    "promoter_name",
    "approved_date",
]


# =============================================================================
# Validation Functions
# =============================================================================


def _validate_pincode(raw_value: str | None) -> str | None:
    if not raw_value:
        return None
    digits = re.sub(r"\D", "", raw_value)
    if not digits:
        return None
    if len(digits) != 6:
        return "Invalid pincode format (expected 6 digits)."
    return None


def validate_price_bounds(
    price: Decimal | float | None,
    field_name: str,
    config: PriceSanityConfig = DEFAULT_PRICE_CONFIG,
) -> list[QAFlag]:
    """
    Validate price against absolute bounds.
    
    Point 27: Price bounds checking.
    """
    flags = []
    
    if price is None:
        return flags
    
    price_decimal = Decimal(str(price))
    
    if "per_sqft" in field_name.lower():
        if price_decimal < config.min_price_per_sqft:
            flags.append(QAFlag(
                flag_type=QAFlagType.PRICE_BELOW_MIN,
                severity="warning",
                message=f"{field_name} below minimum threshold",
                field_name=field_name,
                expected_value=f">= {config.min_price_per_sqft}",
                actual_value=price_decimal,
            ))
        if price_decimal > config.max_price_per_sqft:
            flags.append(QAFlag(
                flag_type=QAFlagType.PRICE_ABOVE_MAX,
                severity="error",
                message=f"{field_name} exceeds maximum threshold",
                field_name=field_name,
                expected_value=f"<= {config.max_price_per_sqft}",
                actual_value=price_decimal,
            ))
    else:
        if price_decimal < config.min_price_total:
            flags.append(QAFlag(
                flag_type=QAFlagType.PRICE_BELOW_MIN,
                severity="warning",
                message=f"{field_name} below minimum threshold",
                field_name=field_name,
                expected_value=f">= {config.min_price_total}",
                actual_value=price_decimal,
            ))
        if price_decimal > config.max_price_total:
            flags.append(QAFlag(
                flag_type=QAFlagType.PRICE_ABOVE_MAX,
                severity="error",
                message=f"{field_name} exceeds maximum threshold",
                field_name=field_name,
                expected_value=f"<= {config.max_price_total}",
                actual_value=price_decimal,
            ))
    
    return flags


def validate_locality_price(
    price_per_sqft: Decimal | float | None,
    locality_avg_price: Decimal | float | None,
    config: PriceSanityConfig = DEFAULT_PRICE_CONFIG,
) -> list[QAFlag]:
    """
    Validate price against locality average.
    
    Point 27: Outlier detection (±30% of locality average).
    """
    flags = []
    
    if price_per_sqft is None or locality_avg_price is None:
        return flags
    
    price = Decimal(str(price_per_sqft))
    locality_avg = Decimal(str(locality_avg_price))
    
    if locality_avg <= 0:
        return flags
    
    deviation = abs(price - locality_avg) / locality_avg
    threshold = Decimal(str(config.locality_deviation_threshold))
    
    if deviation > threshold:
        severity = "error" if deviation > threshold * 2 else "warning"
        flags.append(QAFlag(
            flag_type=QAFlagType.PRICE_LOCALITY_MISMATCH,
            severity=severity,
            message=f"Price deviates {deviation:.1%} from locality average (threshold: {threshold:.0%})",
            field_name="price_per_sqft",
            expected_value=f"{locality_avg} ± {threshold:.0%}",
            actual_value=price,
        ))
    
    return flags


def validate_critical_fields(project_data: dict[str, Any]) -> list[QAFlag]:
    """
    Check for missing critical fields.
    
    Point 27: Auto-flag projects with missing critical fields.
    """
    flags = []
    
    for field in CRITICAL_FIELDS:
        value = project_data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            flags.append(QAFlag(
                flag_type=QAFlagType.MISSING_CRITICAL,
                severity="error",
                message=f"Missing critical field: {field}",
                field_name=field,
                expected_value="non-empty value",
                actual_value=value,
            ))
    
    for field in IMPORTANT_FIELDS:
        value = project_data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            flags.append(QAFlag(
                flag_type=QAFlagType.MISSING_CRITICAL,
                severity="warning",
                message=f"Missing important field: {field}",
                field_name=field,
                expected_value="non-empty value",
                actual_value=value,
            ))
    
    return flags


def validate_area_bounds(
    area_sqft: Decimal | float | None,
    field_name: str,
    config: PriceSanityConfig = DEFAULT_PRICE_CONFIG,
) -> list[QAFlag]:
    """Validate area against reasonable bounds."""
    flags = []
    
    if area_sqft is None:
        return flags
    
    area = Decimal(str(area_sqft))
    
    if area < config.min_area_sqft:
        flags.append(QAFlag(
            flag_type=QAFlagType.BOUNDS_EXCEEDED,
            severity="warning",
            message=f"{field_name} below minimum threshold",
            field_name=field_name,
            expected_value=f">= {config.min_area_sqft}",
            actual_value=area,
        ))
    
    if area > config.max_area_sqft:
        flags.append(QAFlag(
            flag_type=QAFlagType.BOUNDS_EXCEEDED,
            severity="warning",
            message=f"{field_name} exceeds maximum threshold",
            field_name=field_name,
            expected_value=f"<= {config.max_area_sqft}",
            actual_value=area,
        ))
    
    return flags


def validate_date_consistency(
    approved_date: Any,
    proposed_end_date: Any,
    extended_end_date: Any = None,
) -> list[QAFlag]:
    """Validate date field consistency."""
    flags = []
    
    if approved_date and proposed_end_date:
        if proposed_end_date < approved_date:
            flags.append(QAFlag(
                flag_type=QAFlagType.DATA_INCONSISTENCY,
                severity="warning",
                message="Proposed end date is before approved date",
                field_name="proposed_end_date",
                expected_value=f">= {approved_date}",
                actual_value=proposed_end_date,
            ))
    
    if extended_end_date and proposed_end_date:
        if extended_end_date < proposed_end_date:
            flags.append(QAFlag(
                flag_type=QAFlagType.DATA_INCONSISTENCY,
                severity="info",
                message="Extended end date is before proposed end date",
                field_name="extended_end_date",
                expected_value=f">= {proposed_end_date}",
                actual_value=extended_end_date,
            ))
    
    return flags


# =============================================================================
# Main Validation Entry Points
# =============================================================================


def validate_v1_project(project: V1Project) -> list[str]:
    """
    Return a list of validation messages (warnings/errors).
    
    Legacy interface - returns string messages.
    """
    messages: list[str] = []
    details = project.project_details

    if not details.district:
        messages.append("Missing district in project details.")
    if not details.project_status:
        messages.append("Missing project status in project details.")

    raw_pincode = project.raw_data.sections.get("project_details", {}).get("pincode")
    pincode_message = _validate_pincode(raw_pincode)
    if pincode_message:
        messages.append(pincode_message)

    for idx, land in enumerate(project.land_details, start=1):
        if land.land_area_sq_m is not None and land.land_area_sq_m <= 0:
            messages.append(
                f"Land detail {idx}: land_area_sq_m should be a positive number."
            )

    if details.total_area_sq_m is not None and details.total_area_sq_m <= 0:
        messages.append("Project total_area_sq_m should be a positive number.")

    return messages


def run_qa_validation(
    project_data: dict[str, Any],
    locality_avg_price: Decimal | float | None = None,
    config: PriceSanityConfig = DEFAULT_PRICE_CONFIG,
) -> QAResult:
    """
    Run comprehensive QA validation on project data.
    
    Point 27: Full QA gate implementation.
    
    Args:
        project_data: Dictionary with project fields
        locality_avg_price: Optional locality average price for comparison
        config: Price sanity configuration
    
    Returns:
        QAResult with all flags and overall status
    """
    result = QAResult()
    
    # 1. Critical fields check
    for flag in validate_critical_fields(project_data):
        result.add_flag(flag)
    
    # 2. Price bounds check
    for price_field in ["min_price_total", "max_price_total"]:
        price = project_data.get(price_field)
        if price is not None:
            for flag in validate_price_bounds(price, price_field, config):
                result.add_flag(flag)
    
    for price_field in ["min_price_per_sqft", "max_price_per_sqft"]:
        price = project_data.get(price_field)
        if price is not None:
            for flag in validate_price_bounds(price, price_field, config):
                result.add_flag(flag)
    
    # 3. Locality price comparison
    price_per_sqft = project_data.get("price_per_sqft") or project_data.get("min_price_per_sqft")
    if price_per_sqft and locality_avg_price:
        for flag in validate_locality_price(price_per_sqft, locality_avg_price, config):
            result.add_flag(flag)
    
    # 4. Area bounds check
    for area_field in ["carpet_area_sqft", "builtup_area_sqft", "super_builtup_area_sqft"]:
        area = project_data.get(area_field)
        if area is not None:
            for flag in validate_area_bounds(area, area_field, config):
                result.add_flag(flag)
    
    # 5. Date consistency check
    for flag in validate_date_consistency(
        project_data.get("approved_date"),
        project_data.get("proposed_end_date"),
        project_data.get("extended_end_date"),
    ):
        result.add_flag(flag)
    
    # Set final status
    if not result.flags:
        result.status = QAStatus.PASSED
    
    return result


__all__ = [
    "validate_v1_project",
    "run_qa_validation",
    "QAResult",
    "QAFlag",
    "QAFlagType",
    "QAStatus",
    "PriceSanityConfig",
    "DEFAULT_PRICE_CONFIG",
    "validate_price_bounds",
    "validate_locality_price",
    "validate_critical_fields",
    "validate_area_bounds",
    "validate_date_consistency",
]
