"""Amenity-based scoring helpers following PHASE5_AMENITY_DESIGN v1.

The formulas are intentionally simple and transparent so we can tweak
thresholds/weights without re-training any model.  All scores are normalized
on a 0–100 scale and align with the rules in ``docs/PHASE5_AMENITY_DESIGN.md``.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable, Mapping, Sequence

from cg_rera_extractor.db.models import ProjectAmenityStats

ScoreValue = int


@dataclass
class ScoreResult:
    """Container for persisted score fields."""

    amenity_score: ScoreValue
    location_score: ScoreValue
    
    # Location sub-scores
    connectivity_score: ScoreValue
    daily_needs_score: ScoreValue
    social_infra_score: ScoreValue
    
    overall_score: ScoreValue
    score_version: str


@dataclass
class ScoreComputation:
    """Full computation output including diagnostics."""

    scores: ScoreResult
    missing_inputs: set[str]
    inputs_used: dict[str, float | int | None]


@dataclass
class ScoreConfig:
    """Configurable weights and thresholds for the v1 model."""

    score_version: str = "amenity_v1"
    # Target radii (km) for each amenity slice per dimension.
    daily_needs_amenities: Mapping[str, float] = None
    social_infra_amenities: Mapping[str, float] = None
    transit_radii_km: Sequence[float] | None = None
    # Component weights for aggregation.
    connectivity_weight_bank: float = 0.3
    connectivity_weight_transit: float = 0.7
    
    # Weights for location score
    location_weights: Mapping[str, float] | None = None
    
    # Weights for overall score
    overall_weights: Mapping[str, float] | None = None

    def __post_init__(self) -> None:
        # Default mappings mirror the design doc hints.
        if self.daily_needs_amenities is None:
            self.daily_needs_amenities = {
                "grocery_convenience": 1.0,
                "supermarket": 3.0,
                "pharmacy": 1.0,
            }
        if self.social_infra_amenities is None:
            self.social_infra_amenities = {
                "school": 3.0,
                "college_university": 5.0,
                "hospital": 5.0,
                "park_playground": 3.0,
                "restaurant_cafe": 3.0,
                "mall": 5.0,
            }
        if self.transit_radii_km is None:
            self.transit_radii_km = (3.0, 10.0)

        
        if self.location_weights is None:
            self.location_weights = {
                "daily_needs": 0.40,
                "social_infra": 0.35,
                "connectivity": 0.25,
            }

        if self.overall_weights is None:
            self.overall_weights = {
                "amenity": 0.50,
                "location": 0.50,
            }


DEFAULT_SCORE_CONFIG = ScoreConfig()


# ---- Threshold utilities -------------------------------------------------

def _score_from_count(count: int | None, buckets: Sequence[tuple[int, int]]) -> int:
    """Return a bucketed score for a count using inclusive upper bounds.

    ``buckets`` should be sorted by the threshold count (ascending) and contain
    ``(upper_bound_inclusive, score)`` pairs. The last bucket is treated as a
    ceiling for larger values.
    """

    safe_count = 0 if count is None else max(0, count)
    for upper, score in buckets:
        if safe_count <= upper:
            return score
    return buckets[-1][1]


def _score_from_distance(distance_km: float | None, bands: Sequence[tuple[float, int]]) -> int:
    """Return a proximity score given ``(upper_distance_km, score)`` bands."""

    if distance_km is None:
        # Treat unknown distance as if it's beyond the widest band.
        return bands[-1][1]

    for upper, score in bands:
        if distance_km <= upper:
            return score
    return bands[-1][1]


def _clamp_score(value: float) -> int:
    """Clamp to 0–100 and round to nearest integer."""

    return int(max(0, min(100, round(value))))


# ---- Input helpers -------------------------------------------------------

def _index_stats(
    stats: Iterable[ProjectAmenityStats],
) -> dict[str, list[ProjectAmenityStats]]:
    indexed: dict[str, list[ProjectAmenityStats]] = {}
    for stat in stats:
        bucket = indexed.setdefault(stat.amenity_type, [])
        bucket.append(stat)
    return indexed


def _resolve_stat(
    stats: list[ProjectAmenityStats] | None, target_radius_km: float | None
) -> ProjectAmenityStats | None:
    """Pick the stat closest to the requested radius, preferring in-range slices."""

    if not stats:
        return None

    if target_radius_km is None:
        return stats[0]

    within = [s for s in stats if float(s.radius_km) <= target_radius_km]
    if within:
        # Choose the largest radius within the target window for representativeness.
        return sorted(within, key=lambda s: float(s.radius_km), reverse=True)[0]

    # Fallback: pick the smallest available radius.
    return sorted(stats, key=lambda s: float(s.radius_km))[0]


# ---- Dimension computations ---------------------------------------------

def _daily_needs_score(
    stat_index: Mapping[str, list[ProjectAmenityStats]],
    config: ScoreConfig,
    missing: set[str],
    inputs: dict[str, float | int | None],
) -> int:
    buckets = [(0, 20), (2, 60), (4, 80), (5, 100)]
    subscores: list[int] = []

    for amenity_type, radius in config.daily_needs_amenities.items():
        stat = _resolve_stat(stat_index.get(amenity_type), radius)
        count = stat.nearby_count if stat else 0
        if stat is None:
            missing.add(amenity_type)
        score = _score_from_count(count, buckets)
        subscores.append(score)
        inputs[f"{amenity_type}_count"] = 0 if count is None else count

    return _clamp_score(mean(subscores) if subscores else 0)


def _connectivity_score(
    stat_index: Mapping[str, list[ProjectAmenityStats]],
    config: ScoreConfig,
    missing: set[str],
    inputs: dict[str, float | int | None],
) -> int:
    transit_buckets = {
        config.transit_radii_km[0]: [(0, 20), (2, 60), (5, 80), (6, 100)],
        config.transit_radii_km[1]: [(0, 20), (3, 60), (8, 80), (9, 100)],
    }

    transit_scores: list[int] = []
    for radius, buckets in transit_buckets.items():
        stat = _resolve_stat(stat_index.get("transit_stop"), radius)
        count = stat.nearby_count if stat else 0
        if stat is None:
            missing.add(f"transit_stop_{radius}km")
        score = _score_from_count(count, buckets)
        transit_scores.append(score)
        inputs[f"transit_stop_count_{radius}km"] = 0 if count is None else count

    avg_transit = mean(transit_scores) if transit_scores else 0

    bank_stat = _resolve_stat(stat_index.get("bank_atm"), None)
    bank_distance = float(bank_stat.nearby_nearest_km) if (bank_stat and bank_stat.nearby_nearest_km is not None) else None
    if bank_stat is None:
        missing.add("bank_atm")
    inputs["bank_atm_nearest_km"] = bank_distance

    bank_score = _score_from_distance(
        bank_distance, [(1.0, 90), (2.0, 70), (float("inf"), 30)]
    )

    blended = (
        config.connectivity_weight_transit * avg_transit
        + config.connectivity_weight_bank * bank_score
    )
    return _clamp_score(blended)


def _social_infra_score(
    stat_index: Mapping[str, list[ProjectAmenityStats]],
    config: ScoreConfig,
    missing: set[str],
    inputs: dict[str, float | int | None],
) -> int:
    buckets = [(0, 20), (2, 60), (5, 80), (6, 100)]
    subscores: list[int] = []

    hospital_count = 0
    school_count = 0

    for amenity_type, radius in config.social_infra_amenities.items():
        stat = _resolve_stat(stat_index.get(amenity_type), radius)
        count = stat.nearby_count if stat else 0
        if stat is None:
            missing.add(amenity_type)
        score = _score_from_count(count, buckets)
        subscores.append(score)
        inputs[f"{amenity_type}_count"] = 0 if count is None else count

        if amenity_type == "hospital":
            hospital_count = 0 if count is None else count
        if amenity_type == "school":
            school_count = 0 if count is None else count

    base_score = mean(subscores) if subscores else 0

    # Cap the score if both hospitals and schools are missing per design hint.
    if hospital_count == 0 and school_count == 0:
        base_score = min(base_score, 70)

    return _clamp_score(base_score)


# ---- Public API ----------------------------------------------------------

def compute_amenity_scores(
    amenity_stats: Iterable[ProjectAmenityStats],
    config: ScoreConfig = DEFAULT_SCORE_CONFIG,
) -> ScoreComputation:
    """Compute amenity-driven scores for a project.

    The implementation mirrors the v1 rules in ``PHASE5_AMENITY_DESIGN.md``:
    - Daily needs: bucketed counts for groceries/supermarkets/pharmacies.
    - Connectivity: weighted blend of transit availability (3 km & 10 km) and
      bank/ATM proximity as a light proxy for road frontage.
    - Social infrastructure: bucketed counts across education, healthcare, open
      spaces, and leisure; optionally capped when hospital and school are both
      absent.
    - Overall: 40% daily needs, 35% social infra, 25% connectivity.
    """

    stat_index = _index_stats(amenity_stats)
    missing_inputs: set[str] = set()
    inputs_used: dict[str, float | int | None] = {}

    daily_needs = _daily_needs_score(stat_index, config, missing_inputs, inputs_used)
    connectivity = _connectivity_score(stat_index, config, missing_inputs, inputs_used)
    social_infra = _social_infra_score(stat_index, config, missing_inputs, inputs_used)

    # Location Score (Composite of the above)
    loc_weights = config.location_weights
    location_score = _clamp_score(
        daily_needs * loc_weights.get("daily_needs", 0)
        + social_infra * loc_weights.get("social_infra", 0)
        + connectivity * loc_weights.get("connectivity", 0)
    )
    
    # Amenity Score (Onsite)
    # Placeholder: For now, we don't have onsite data populated, so we default to 0 or a placeholder.
    # Once RERA data is ingested, we will compute this from `onsite_available` flags.
    amenity_score = 0 
    
    # Overall Score
    overall_weights = config.overall_weights
    overall = _clamp_score(
        amenity_score * overall_weights.get("amenity", 0)
        + location_score * overall_weights.get("location", 0)
    )

    scores = ScoreResult(
        amenity_score=amenity_score,
        location_score=location_score,
        connectivity_score=connectivity,
        daily_needs_score=daily_needs,
        social_infra_score=social_infra,
        overall_score=overall,
        score_version=config.score_version,
    )

    return ScoreComputation(scores=scores, missing_inputs=missing_inputs, inputs_used=inputs_used)


__all__ = ["ScoreResult", "ScoreConfig", "ScoreComputation", "compute_amenity_scores"]
