"""Amenity provider abstraction and caching utilities."""

from .provider import (
    Amenity,
    AmenityProvider,
    OSMOverpassProvider,
    get_provider_from_config,
)
from .cache import AmenityCache
from .stats import AmenitySliceStats, compute_project_amenity_stats, to_orm_rows
from .scoring import (
    ScoreComputation,
    ScoreConfig,
    ScoreResult,
    compute_amenity_scores,
)

__all__ = [
    "Amenity",
    "AmenityProvider",
    "OSMOverpassProvider",
    "get_provider_from_config",
    "AmenityCache",
    "AmenitySliceStats",
    "compute_project_amenity_stats",
    "to_orm_rows",
    "ScoreResult",
    "ScoreConfig",
    "ScoreComputation",
    "compute_amenity_scores",
]
