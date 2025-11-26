"""Score explanation helper for generating human-readable explanations of project scores.

This module provides functions to produce a structured JSON-serializable explanation
of why a project received a particular overall_score, based on amenity and location data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session, selectinload

from cg_rera_extractor.db.models import Project, ProjectAmenityStats, ProjectScores


@dataclass
class ScoreFactors:
    """Factors contributing to score broken down by category."""
    
    onsite: dict[str, list[str]] = field(default_factory=lambda: {"strong": [], "weak": []})
    location: dict[str, list[str]] = field(default_factory=lambda: {"strong": [], "weak": []})


@dataclass
class ScoreExplanation:
    """Structured explanation of a project's score."""
    
    summary: str
    positives: list[str]
    negatives: list[str]
    factors: ScoreFactors
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "summary": self.summary,
            "positives": self.positives,
            "negatives": self.negatives,
            "factors": {
                "onsite": {
                    "strong": self.factors.onsite["strong"],
                    "weak": self.factors.onsite["weak"],
                },
                "location": {
                    "strong": self.factors.location["strong"],
                    "weak": self.factors.location["weak"],
                },
            },
        }


# Thresholds for determining strong/weak amenities
ONSITE_STRONG_THRESHOLD = 0.70  # >= 70% complete is considered strong
ONSITE_WEAK_THRESHOLD = 0.30   # < 30% complete is considered weak

# Location context thresholds
NEARBY_COUNT_GOOD: dict[str, int] = {
    "school": 3,
    "hospital": 2,
    "grocery_convenience": 2,
    "supermarket": 1,
    "pharmacy": 2,
    "transit_stop": 3,
    "bank_atm": 1,
    "park_playground": 1,
    "restaurant_cafe": 2,
}

NEARBY_DISTANCE_GOOD_KM: dict[str, float] = {
    "school": 3.0,
    "hospital": 5.0,
    "grocery_convenience": 1.5,
    "supermarket": 3.0,
    "pharmacy": 2.0,
    "transit_stop": 2.0,
    "bank_atm": 2.0,
    "park_playground": 2.0,
}

# Amenity type display names
AMENITY_DISPLAY_NAMES: dict[str, str] = {
    "school": "Schools",
    "hospital": "Hospitals",
    "grocery_convenience": "Grocery stores",
    "supermarket": "Supermarkets",
    "pharmacy": "Pharmacies",
    "transit_stop": "Transit stops",
    "bank_atm": "Banks/ATMs",
    "park_playground": "Parks",
    "restaurant_cafe": "Restaurants/Cafés",
    "college_university": "Colleges",
    "mall": "Malls",
    # Onsite amenities
    "internal_roads": "Internal roads",
    "water_supply": "Water supply",
    "sewerage": "Sewerage",
    "electricity": "Electricity",
    "clubhouse": "Clubhouse",
    "park": "Park",
    "swimming_pool": "Swimming pool",
    "gymnasium": "Gymnasium",
    "parking": "Parking",
}


def _to_float(value: Decimal | float | int | None) -> float | None:
    """Safely convert a numeric value to float."""
    if value is None:
        return None
    return float(value)


def _format_amenity_name(amenity_type: str) -> str:
    """Format amenity type for display."""
    return AMENITY_DISPLAY_NAMES.get(amenity_type, amenity_type.replace("_", " ").title())


def _analyze_onsite_amenities(
    stats: list[ProjectAmenityStats],
) -> tuple[list[str], list[str], dict[str, list[str]]]:
    """Analyze onsite amenities and return positives, negatives, and factor lists."""
    
    positives: list[str] = []
    negatives: list[str] = []
    factors: dict[str, list[str]] = {"strong": [], "weak": []}
    
    onsite_stats = [s for s in stats if s.radius_km is None]
    
    for stat in onsite_stats:
        amenity_name = _format_amenity_name(stat.amenity_type)
        
        # Check if onsite_details has progress information
        progress: float | None = None
        if stat.onsite_details and isinstance(stat.onsite_details, dict):
            progress = stat.onsite_details.get("progress")
            if progress is None:
                progress = stat.onsite_details.get("completion_percentage")
            if progress is not None:
                # Normalize to 0-1 if given as percentage
                if progress > 1:
                    progress = progress / 100.0
        
        if stat.onsite_available:
            if progress is not None:
                if progress >= ONSITE_STRONG_THRESHOLD:
                    factors["strong"].append(stat.amenity_type)
                    positives.append(f"{amenity_name} available ({int(progress * 100)}% complete)")
                elif progress < ONSITE_WEAK_THRESHOLD:
                    factors["weak"].append(stat.amenity_type)
                    negatives.append(f"{amenity_name} reported but only {int(progress * 100)}% complete")
                else:
                    # Moderate progress, don't highlight as strong or weak
                    pass
            else:
                # Available but no progress data - treat as a positive
                factors["strong"].append(stat.amenity_type)
                positives.append(f"{amenity_name} available")
        else:
            # Not available - only flag if it's a key amenity
            key_onsite = {"internal_roads", "water_supply", "sewerage", "electricity", "parking"}
            if stat.amenity_type in key_onsite:
                factors["weak"].append(stat.amenity_type)
                negatives.append(f"{amenity_name} not available")
    
    return positives, negatives, factors


def _analyze_location_context(
    stats: list[ProjectAmenityStats],
) -> tuple[list[str], list[str], dict[str, list[str]]]:
    """Analyze location/nearby amenities and return positives, negatives, and factor lists."""
    
    positives: list[str] = []
    negatives: list[str] = []
    factors: dict[str, list[str]] = {"strong": [], "weak": []}
    
    # Group nearby stats by amenity type, taking the best (smallest radius) stat for each
    nearby_by_type: dict[str, ProjectAmenityStats] = {}
    for stat in stats:
        if stat.radius_km is None:
            continue
        existing = nearby_by_type.get(stat.amenity_type)
        if existing is None or (stat.radius_km and existing.radius_km and float(stat.radius_km) < float(existing.radius_km)):
            nearby_by_type[stat.amenity_type] = stat
    
    for amenity_type, stat in nearby_by_type.items():
        amenity_name = _format_amenity_name(amenity_type)
        count = stat.nearby_count or 0
        nearest_km = _to_float(stat.nearby_nearest_km)
        radius_km = _to_float(stat.radius_km)
        
        good_count = NEARBY_COUNT_GOOD.get(amenity_type, 2)
        good_distance = NEARBY_DISTANCE_GOOD_KM.get(amenity_type, 3.0)
        
        if count >= good_count:
            factors["strong"].append(amenity_type)
            if nearest_km is not None and radius_km is not None:
                positives.append(
                    f"{count} {amenity_name.lower()} within {radius_km:.0f}km; nearest {nearest_km:.1f}km"
                )
            else:
                positives.append(f"{count} {amenity_name.lower()} nearby")
        elif count == 0:
            factors["weak"].append(amenity_type)
            if radius_km is not None:
                negatives.append(f"No {amenity_name.lower()} within {radius_km:.0f}km")
            else:
                negatives.append(f"No {amenity_name.lower()} nearby")
        elif count == 1 and nearest_km is not None and nearest_km > good_distance:
            factors["weak"].append(amenity_type)
            negatives.append(f"Only 1 {amenity_name.lower()} (~{nearest_km:.1f}km away)")
    
    return positives, negatives, factors


def _generate_summary(
    scores: ProjectScores | None,
    onsite_positives: list[str],
    onsite_negatives: list[str],
    location_positives: list[str],
    location_negatives: list[str],
) -> str:
    """Generate a brief summary of the score."""
    
    if scores is None:
        return "Score data not available"
    
    location_score = _to_float(scores.location_score)
    amenity_score = _to_float(scores.amenity_score)
    
    # Determine location quality
    location_quality = "unknown"
    if location_score is not None:
        if location_score >= 75:
            location_quality = "excellent"
        elif location_score >= 50:
            location_quality = "good"
        elif location_score >= 30:
            location_quality = "moderate"
        else:
            location_quality = "limited"
    
    # Determine amenity quality
    amenity_quality = "unknown"
    if amenity_score is not None:
        if amenity_score >= 75:
            amenity_quality = "strong"
        elif amenity_score >= 50:
            amenity_quality = "moderate"
        elif amenity_score >= 30:
            amenity_quality = "basic"
        else:
            amenity_quality = "limited"
    
    # Build summary
    parts = []
    if location_quality != "unknown":
        parts.append(f"{location_quality.capitalize()} location")
    if amenity_quality != "unknown":
        parts.append(f"{amenity_quality} onsite infrastructure")
    
    if parts:
        return ", ".join(parts)
    
    return "Score calculated with available data"


def explain_project_score(
    project_id: int,
    session: Session,
) -> dict[str, Any]:
    """Generate an explanation for a project's score.
    
    Args:
        project_id: The database ID of the project.
        session: SQLAlchemy database session.
    
    Returns:
        A JSON-serializable dictionary with the score explanation.
    """
    
    # Fetch project with related data
    project = (
        session.query(Project)
        .options(
            selectinload(Project.score),
            selectinload(Project.amenity_stats),
        )
        .filter(Project.id == project_id)
        .one_or_none()
    )
    
    if project is None:
        return {
            "summary": "Project not found",
            "positives": [],
            "negatives": ["Project does not exist in the database"],
            "factors": {"onsite": {"strong": [], "weak": []}, "location": {"strong": [], "weak": []}},
        }
    
    scores: ProjectScores | None = project.score
    stats: list[ProjectAmenityStats] = list(project.amenity_stats)
    
    # Handle insufficient data case
    if scores is None or scores.score_status == "insufficient_data":
        reason = "Missing amenity or location context data"
        if scores and scores.score_status_reason:
            if isinstance(scores.score_status_reason, list):
                reason = ", ".join(scores.score_status_reason)
            elif isinstance(scores.score_status_reason, dict):
                reason = ", ".join(str(v) for v in scores.score_status_reason.values())
            else:
                reason = str(scores.score_status_reason)
        
        return {
            "summary": "Not enough data to explain score",
            "positives": [],
            "negatives": [reason],
            "factors": {"onsite": {"strong": [], "weak": []}, "location": {"strong": [], "weak": []}},
        }
    
    # Analyze onsite amenities
    onsite_positives, onsite_negatives, onsite_factors = _analyze_onsite_amenities(stats)
    
    # Analyze location context
    location_positives, location_negatives, location_factors = _analyze_location_context(stats)
    
    # Combine and limit to top 2-3 each
    all_positives = location_positives + onsite_positives
    all_negatives = location_negatives + onsite_negatives
    
    top_positives = all_positives[:3]
    top_negatives = all_negatives[:3]
    
    # Generate summary
    summary = _generate_summary(
        scores,
        onsite_positives,
        onsite_negatives,
        location_positives,
        location_negatives,
    )
    
    explanation = ScoreExplanation(
        summary=summary,
        positives=top_positives,
        negatives=top_negatives,
        factors=ScoreFactors(
            onsite=onsite_factors,
            location=location_factors,
        ),
    )
    
    return explanation.to_dict()


__all__ = ["explain_project_score", "ScoreExplanation", "ScoreFactors"]
