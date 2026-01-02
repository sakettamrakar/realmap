"""Project detail service assembling enriched payloads."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, selectinload

from cg_rera_extractor.amenities.value_scoring import compute_value_score, get_value_bucket
from cg_rera_extractor.analysis.explain import explain_project_score
from cg_rera_extractor.db import Project, ProjectAmenityStats, ProjectScores

from .search import _nearby_counts, _onsite_amenities, _resolve_location, _score_to_float, _get_latest_price
from .jsonld import generate_project_jsonld


def _build_amenities_section(stats: list[ProjectAmenityStats]) -> dict[str, Any]:
    onsite_list = [s.amenity_type for s in stats if s.radius_km is None and s.onsite_available]
    onsite_counts = {
        "total": len(onsite_list),
        "primary": len(onsite_list),
        "secondary": 0,
    }

    nearby_summary = {k: {"count": v} for k, v in _nearby_counts(stats).items()}

    return {
        "onsite_list": onsite_list,
        "onsite_counts": onsite_counts,
        "nearby_summary": nearby_summary,
    }


def fetch_project_detail(db: Session, project_id: int) -> dict[str, Any] | None:
    """Return a project detail payload or ``None`` if missing."""

    project = (
        db.query(Project)
        .options(
            selectinload(Project.score),
            selectinload(Project.amenity_stats),
            selectinload(Project.locations),
            selectinload(Project.promoters),
            selectinload(Project.buildings),
            selectinload(Project.unit_types),
            selectinload(Project.documents),
            selectinload(Project.quarterly_updates),
            selectinload(Project.pricing_snapshots),
            selectinload(Project.project_unit_types),
        )
        .filter(Project.id == project_id)
        .one_or_none()
    )

    if not project:
        return None

    lat, lon, quality = _resolve_location(project)
    scores: ProjectScores | None = project.score
    highlight, onsite_counts = _onsite_amenities(project.amenity_stats)

    amenity_section = _build_amenities_section(project.amenity_stats)
    amenity_section["onsite_list"] = highlight
    amenity_section["onsite_counts"] = onsite_counts | {"secondary": amenity_section["onsite_counts"].get("secondary", 0)}

    price_info = _get_latest_price(project)
    
    # Compute value_score if we have the necessary data
    # Use stored value if available, otherwise compute on the fly
    value_score = None
    if scores and scores.value_score is not None:
        value_score = _score_to_float(scores.value_score)
    elif scores and scores.overall_score is not None and price_info.get("min_price_total"):
        value_score = compute_value_score(
            _score_to_float(scores.overall_score),
            price_info.get("min_price_total"),
            price_info.get("max_price_total"),
        )
    
    value_bucket = get_value_bucket(value_score)
    
    # Build unit types list from new table or fallback to old?
    # Let's use new table if available, else old.
    unit_types = []
    if project.project_unit_types:
        for ut in project.project_unit_types:
            if ut.is_active:
                unit_types.append({
                    "label": ut.unit_label,
                    "bedrooms": ut.bedrooms,
                    "area_range": [float(ut.carpet_area_min_sqft) if ut.carpet_area_min_sqft else None, 
                                   float(ut.carpet_area_max_sqft) if ut.carpet_area_max_sqft else None],
                })
    elif project.unit_types:
        for ut in project.unit_types:
            unit_types.append({
                "label": ut.type_name,
                "bedrooms": None, # Old schema doesn't have bedrooms explicitly
                "area_range": [float(ut.carpet_area_sqmt * 10.764) if ut.carpet_area_sqmt else None, None], # Convert sqmt to sqft
            })

    other_registrations = []
    if project.parent_project_id:
        others = (
            db.query(Project)
            .filter(Project.parent_project_id == project.parent_project_id)
            .filter(Project.id != project.id)
            .all()
        )
        for other in others:
            other_registrations.append({
                "project_id": other.id,
                "rera_number": other.rera_registration_number,
                "status": other.status,
                "registration_date": other.approved_date.isoformat() if other.approved_date else None,
            })

    payload: dict[str, Any] = {
        "project": {
            "project_id": project.id,
            "parent_project_id": project.parent_project_id,
            "other_registrations": other_registrations,
            "name": project.project_name,
            "rera_number": project.rera_registration_number,
            "developer": None,
            "project_type": project.project_name,
            "status": project.status,
            "registration_date": project.approved_date,
            "expected_completion": project.proposed_end_date or project.extended_end_date,
            "rera_fields": project.raw_data_json,
        },
        "location": {
            "lat": lat,
            "lon": lon,
            "geo_source": project.geo_source or project.geocoding_source or quality,
            "geo_confidence": project.geo_precision,
            "address": project.full_address or project.normalized_address,
            "district": project.district,
            "tehsil": project.tehsil,
        },
        "scores": {
            "overall_score": _score_to_float(scores.overall_score) if scores else None,
            "location_score": _score_to_float(scores.location_score) if scores else None,
            "amenity_score": _score_to_float(scores.amenity_score) if scores else None,
            "value_score": value_score,
            "value_bucket": value_bucket,
            "score_status": scores.score_status if scores else None,
            "score_status_reason": scores.score_status_reason if scores else None,
            "scoring_version": scores.score_version if scores else None,
        },
        "amenities": amenity_section,
        "pricing": {
            "min_price_total": price_info.get("min_price_total"),
            "max_price_total": price_info.get("max_price_total"),
            "min_price_per_sqft": price_info.get("min_price_per_sqft"),
            "max_price_per_sqft": price_info.get("max_price_per_sqft"),
            "unit_types": unit_types,
        },
        "qa": {
            "geo_notes": project.geo_normalized_address,
            "amenity_notes": None,
            "issues": [],
        },
        "score_explanation": explain_project_score(project.id, db),
        
        # Point 17: Data Provenance
        "provenance": {
            "last_updated_at": project.scraped_at.isoformat() if project.scraped_at else None,
            "source_domain": "rera.cg.gov.in",
            "extraction_method": "scraper",
            "confidence_score": float(project.geo_confidence) if project.geo_confidence else None,
            "data_quality_score": project.data_quality_score,
            "last_parsed_at": project.last_parsed_at.isoformat() if project.last_parsed_at else None,
        },
        
        # Point 15: JSON-LD for SEO
        "schema_org": generate_project_jsonld(
            project=project,
            scores=scores,
            pricing=price_info,
        ).model_dump(by_alias=True, exclude_none=True),
    }

    return payload


__all__ = ["fetch_project_detail"]
