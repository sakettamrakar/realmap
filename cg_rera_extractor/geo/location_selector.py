"""Logic to select the canonical location for a project from multiple candidates."""

from __future__ import annotations

import logging

from cg_rera_extractor.db import Project, ProjectLocation

logger = logging.getLogger(__name__)

# Priority order for source types (lower value = higher priority)
SOURCE_PRIORITY = {
    "manual_pin": 10,
    "rera_pin": 20,
    "geocode_normalized": 30,
    "district_centroid": 40,
    "tehsil_centroid": 50,
    "other": 100,
}

# Priority adjustment for precision (lower value = higher priority)
# This is added to the source priority.
PRECISION_PRIORITY = {
    "exact": 0,
    "locality": 1,
    "town": 4,
    "city": 5,
    "district": 6,
    "state": 7,
    "unknown": 9,
}


def _get_priority_score(location: ProjectLocation) -> int:
    """Calculate a priority score for a location (lower is better)."""
    base_score = SOURCE_PRIORITY.get(location.source_type, 100)
    
    # For geocoded results, precision matters a lot
    precision_score = PRECISION_PRIORITY.get(location.precision_level or "unknown", 9)
    
    # If it's a manual or RERA pin, we generally trust it regardless of precision label,
    # but for geocoding, we want to penalize rough matches.
    if location.source_type == "geocode_normalized":
        return base_score + precision_score
    
    return base_score


def select_canonical_location(project: Project) -> ProjectLocation | None:
    """
    Select the best available location for a project.
    
    Returns the ProjectLocation object that should be considered canonical.
    """
    if not project.locations:
        return None

    active_locations = [loc for loc in project.locations if loc.is_active]
    if not active_locations:
        return None

    # Sort by:
    # 1. Priority Score (asc)
    # 2. Confidence Score (desc) - handle None as 0
    # 3. Created At (desc) - latest first
    
    def sort_key(loc: ProjectLocation):
        prio = _get_priority_score(loc)
        conf = float(loc.confidence_score or 0)
        # We want descending confidence, so negate it (or use reverse=True but prio is asc)
        # Let's construct a tuple for ascending sort:
        # (priority_score, -confidence, -timestamp)
        ts = loc.created_at.timestamp() if loc.created_at else 0
        return (prio, -conf, -ts)

    sorted_locs = sorted(active_locations, key=sort_key)
    best = sorted_locs[0]
    
    logger.debug(
        "Selected location %s (source=%s, precision=%s) for project %s from %d candidates",
        best.id,
        best.source_type,
        best.precision_level,
        project.id,
        len(active_locations),
    )
    return best


def apply_canonical_location(project: Project, location: ProjectLocation | None) -> bool:
    """
    Apply the given location as the canonical location for the project.
    Returns True if changes were made.
    """
    if not location:
        # We generally don't clear existing data if no location is found, 
        # unless we strictly want to enforce sync. For now, do nothing.
        return False

    def is_diff(val1, val2):
        if val1 is None and val2 is None: return False
        if val1 is None or val2 is None: return True
        return float(val1) != float(val2)

    changed = (
        is_diff(project.latitude, location.lat) or
        is_diff(project.longitude, location.lon) or
        project.geo_source != location.source_type or
        project.geo_precision != location.precision_level
    )

    if changed:
        project.latitude = location.lat
        project.longitude = location.lon
        project.geo_source = location.source_type
        project.geo_precision = location.precision_level
        project.geo_confidence = location.confidence_score
        
        if location.meta_data and "formatted_address" in location.meta_data:
            project.geo_formatted_address = location.meta_data["formatted_address"]
            
    return changed
