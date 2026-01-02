"""
Enrichment Module for Data Merging

Merges PDF-extracted data with scraped metadata to create
enriched project records.

Components:
- DataMerger: Merge PDF extractions with scraped data
- ConflictResolver: Resolve conflicts between data sources
"""

from .data_merger import DataMerger, MergeResult
from .conflict_resolver import ConflictResolver, ConflictResolution

__all__ = [
    "DataMerger",
    "MergeResult",
    "ConflictResolver",
    "ConflictResolution",
]
