"""
Conflict Resolution for Data Merging

Handles conflicts when the same field has different values
from different data sources (scraped vs PDF-extracted).
"""

import re
import logging
from enum import Enum
from typing import Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class ResolutionStrategy(Enum):
    """Strategy for resolving conflicts"""
    PREFER_PDF = "prefer_pdf"  # PDF data takes precedence
    PREFER_SCRAPED = "prefer_scraped"  # Scraped data takes precedence
    PREFER_LONGER = "prefer_longer"  # Prefer longer/more complete value
    PREFER_NEWER = "prefer_newer"  # Prefer more recent date
    MERGE = "merge"  # Combine both values
    MANUAL = "manual"  # Flag for manual review


@dataclass
class ConflictResolution:
    """Result of conflict resolution"""
    field_name: str
    scraped_value: Any
    pdf_value: Any
    resolved_value: Any
    strategy_used: ResolutionStrategy
    confidence: float
    needs_review: bool = False
    notes: str = ""


class ConflictResolver:
    """
    Resolves conflicts between scraped and PDF-extracted data.
    
    Uses field-specific strategies to determine which value to use
    when there are discrepancies.
    
    Usage:
        resolver = ConflictResolver()
        resolution = resolver.resolve("project_name", scraped_value, pdf_value)
        final_value = resolution.resolved_value
    """
    
    # Field-specific strategies
    FIELD_STRATEGIES = {
        # Registration info - PDF is authoritative
        "registration_number": ResolutionStrategy.PREFER_PDF,
        "registration_date": ResolutionStrategy.PREFER_PDF,
        "valid_till": ResolutionStrategy.PREFER_PDF,
        "valid_from": ResolutionStrategy.PREFER_PDF,
        
        # Project info - prefer longer/more complete
        "project_name": ResolutionStrategy.PREFER_LONGER,
        "project_address": ResolutionStrategy.PREFER_LONGER,
        "promoter_name": ResolutionStrategy.PREFER_LONGER,
        "promoter_address": ResolutionStrategy.PREFER_LONGER,
        
        # Numeric fields - PDF is authoritative
        "total_units": ResolutionStrategy.PREFER_PDF,
        "total_plots": ResolutionStrategy.PREFER_PDF,
        "total_land_area": ResolutionStrategy.PREFER_PDF,
        
        # Bank details - PDF is authoritative
        "account_number": ResolutionStrategy.PREFER_PDF,
        "ifsc_code": ResolutionStrategy.PREFER_PDF,
        "bank_name": ResolutionStrategy.PREFER_PDF,
        
        # Default for unspecified fields
        "_default": ResolutionStrategy.PREFER_PDF,
    }
    
    def __init__(self, default_strategy: ResolutionStrategy = ResolutionStrategy.PREFER_PDF):
        """
        Initialize conflict resolver.
        
        Args:
            default_strategy: Default strategy for unspecified fields
        """
        self.default_strategy = default_strategy
    
    def resolve(
        self,
        field_name: str,
        scraped_value: Any,
        pdf_value: Any,
        force_strategy: Optional[ResolutionStrategy] = None
    ) -> ConflictResolution:
        """
        Resolve conflict for a single field.
        
        Args:
            field_name: Name of the field
            scraped_value: Value from scraped data
            pdf_value: Value from PDF extraction
            force_strategy: Override the default strategy
            
        Returns:
            ConflictResolution with resolved value
        """
        # If one is None/empty, use the other
        scraped_empty = self._is_empty(scraped_value)
        pdf_empty = self._is_empty(pdf_value)
        
        if scraped_empty and pdf_empty:
            return ConflictResolution(
                field_name=field_name,
                scraped_value=scraped_value,
                pdf_value=pdf_value,
                resolved_value=None,
                strategy_used=ResolutionStrategy.PREFER_PDF,
                confidence=1.0,
                notes="Both values empty"
            )
        
        if scraped_empty:
            return ConflictResolution(
                field_name=field_name,
                scraped_value=scraped_value,
                pdf_value=pdf_value,
                resolved_value=pdf_value,
                strategy_used=ResolutionStrategy.PREFER_PDF,
                confidence=1.0,
                notes="Scraped value empty, using PDF"
            )
        
        if pdf_empty:
            return ConflictResolution(
                field_name=field_name,
                scraped_value=scraped_value,
                pdf_value=pdf_value,
                resolved_value=scraped_value,
                strategy_used=ResolutionStrategy.PREFER_SCRAPED,
                confidence=1.0,
                notes="PDF value empty, using scraped"
            )
        
        # Both have values - check if they match
        if self._values_match(scraped_value, pdf_value):
            return ConflictResolution(
                field_name=field_name,
                scraped_value=scraped_value,
                pdf_value=pdf_value,
                resolved_value=pdf_value,  # Use PDF as canonical
                strategy_used=ResolutionStrategy.PREFER_PDF,
                confidence=1.0,
                notes="Values match"
            )
        
        # Values conflict - apply strategy
        strategy = force_strategy or self.FIELD_STRATEGIES.get(
            field_name,
            self.default_strategy
        )
        
        resolved, confidence, notes = self._apply_strategy(
            strategy, scraped_value, pdf_value, field_name
        )
        
        needs_review = confidence < 0.7
        
        return ConflictResolution(
            field_name=field_name,
            scraped_value=scraped_value,
            pdf_value=pdf_value,
            resolved_value=resolved,
            strategy_used=strategy,
            confidence=confidence,
            needs_review=needs_review,
            notes=notes
        )
    
    def _is_empty(self, value: Any) -> bool:
        """Check if value is empty/None"""
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        return False
    
    def _values_match(self, v1: Any, v2: Any) -> bool:
        """Check if two values are equivalent"""
        # Direct equality
        if v1 == v2:
            return True
        
        # String comparison (case-insensitive, whitespace-normalized)
        if isinstance(v1, str) and isinstance(v2, str):
            n1 = ' '.join(v1.lower().split())
            n2 = ' '.join(v2.lower().split())
            if n1 == n2:
                return True
            # Check if one contains the other (for abbreviations)
            if n1 in n2 or n2 in n1:
                return True
        
        return False
    
    def _apply_strategy(
        self,
        strategy: ResolutionStrategy,
        scraped: Any,
        pdf: Any,
        field_name: str
    ) -> Tuple[Any, float, str]:
        """
        Apply resolution strategy.
        
        Returns: (resolved_value, confidence, notes)
        """
        if strategy == ResolutionStrategy.PREFER_PDF:
            return pdf, 0.9, "Preferred PDF value"
        
        elif strategy == ResolutionStrategy.PREFER_SCRAPED:
            return scraped, 0.9, "Preferred scraped value"
        
        elif strategy == ResolutionStrategy.PREFER_LONGER:
            s_len = len(str(scraped)) if scraped else 0
            p_len = len(str(pdf)) if pdf else 0
            
            if p_len > s_len:
                return pdf, 0.8, f"PDF value longer ({p_len} vs {s_len} chars)"
            elif s_len > p_len:
                return scraped, 0.8, f"Scraped value longer ({s_len} vs {p_len} chars)"
            else:
                return pdf, 0.7, "Same length, defaulting to PDF"
        
        elif strategy == ResolutionStrategy.PREFER_NEWER:
            s_date = self._parse_date(scraped)
            p_date = self._parse_date(pdf)
            
            if s_date and p_date:
                if p_date > s_date:
                    return pdf, 0.8, "PDF date is newer"
                else:
                    return scraped, 0.8, "Scraped date is newer"
            return pdf, 0.6, "Could not compare dates"
        
        elif strategy == ResolutionStrategy.MERGE:
            # For lists, combine
            if isinstance(scraped, list) and isinstance(pdf, list):
                merged = list(set(scraped + pdf))
                return merged, 0.8, "Merged lists"
            
            # For strings, concatenate if different
            if isinstance(scraped, str) and isinstance(pdf, str):
                return f"{scraped} | {pdf}", 0.5, "Concatenated values (needs review)"
            
            return pdf, 0.6, "Could not merge, using PDF"
        
        elif strategy == ResolutionStrategy.MANUAL:
            return pdf, 0.3, "Flagged for manual review"
        
        # Default
        return pdf, 0.7, "Default resolution"
    
    def _parse_date(self, value: Any) -> Optional[datetime]:
        """Try to parse a date value"""
        if isinstance(value, datetime):
            return value
        
        if not isinstance(value, str):
            return None
        
        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        
        return None
    
    def resolve_all(
        self,
        scraped_data: dict,
        pdf_data: dict,
        fields: Optional[list] = None
    ) -> dict[str, ConflictResolution]:
        """
        Resolve conflicts for multiple fields.
        
        Args:
            scraped_data: Dictionary of scraped values
            pdf_data: Dictionary of PDF-extracted values
            fields: Specific fields to resolve (None = all)
            
        Returns:
            Dictionary of field_name -> ConflictResolution
        """
        if fields is None:
            fields = set(scraped_data.keys()) | set(pdf_data.keys())
        
        resolutions = {}
        for field in fields:
            scraped_value = scraped_data.get(field)
            pdf_value = pdf_data.get(field)
            resolutions[field] = self.resolve(field, scraped_value, pdf_value)
        
        return resolutions
