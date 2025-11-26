"""Admin/debug routes for internal project inspection."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from cg_rera_extractor.api.deps import get_db
from cg_rera_extractor.api.services import fetch_project_detail
from cg_rera_extractor.db import Project, ProjectArtifact
from sqlalchemy.orm import Session, selectinload

router = APIRouter(prefix="/admin", tags=["admin"])

# Base outputs directory - can be configured via environment variable
OUTPUTS_BASE = Path(os.environ.get("OUTPUTS_DIR", "outputs"))


def _find_project_artifacts(project: Project, db: Session) -> dict[str, Any]:
    """Find all artifacts associated with a project."""
    
    # Get artifacts from DB
    db_artifacts = (
        db.query(ProjectArtifact)
        .filter(ProjectArtifact.project_id == project.id)
        .all()
    )
    
    artifact_list = []
    for artifact in db_artifacts:
        artifact_list.append({
            "id": artifact.id,
            "category": artifact.category,
            "artifact_type": artifact.artifact_type,
            "file_path": artifact.file_path,
            "source_url": artifact.source_url,
            "file_format": artifact.file_format,
            "is_preview": artifact.is_preview,
        })
    
    return {"db_artifacts": artifact_list}


def _find_file_artifacts(rera_number: str) -> dict[str, Any]:
    """Search for files related to a project in the outputs directory."""
    
    # Normalize the RERA number for file matching
    rera_clean = rera_number.replace("/", "_").replace("\\", "_")
    
    file_artifacts = {
        "scraped_json": [],
        "raw_html": [],
        "raw_extracted": [],
        "previews": [],
        "listings": [],
    }
    
    # Search through all run directories
    runs_paths = [
        OUTPUTS_BASE / "realcrawl" / "runs",
        OUTPUTS_BASE / "demo-run",
        OUTPUTS_BASE / "test-1project",
        OUTPUTS_BASE / "debug_runs",
    ]
    
    for runs_base in runs_paths:
        if not runs_base.exists():
            continue
            
        # Handle both direct runs and nested run directories
        if runs_base.name == "runs":
            run_dirs = [d for d in runs_base.iterdir() if d.is_dir()]
        else:
            run_dirs = [runs_base]
        
        for run_dir in run_dirs:
            # Check scraped_json
            scraped_dir = run_dir / "scraped_json"
            if scraped_dir.exists():
                for f in scraped_dir.glob(f"*{rera_clean}*"):
                    file_artifacts["scraped_json"].append({
                        "path": str(f.relative_to(OUTPUTS_BASE)),
                        "full_path": str(f),
                        "run": run_dir.name,
                        "size_bytes": f.stat().st_size if f.exists() else 0,
                    })
            
            # Check raw_html
            html_dir = run_dir / "raw_html"
            if html_dir.exists():
                for f in html_dir.glob(f"*{rera_clean}*"):
                    file_artifacts["raw_html"].append({
                        "path": str(f.relative_to(OUTPUTS_BASE)),
                        "full_path": str(f),
                        "run": run_dir.name,
                        "size_bytes": f.stat().st_size if f.exists() else 0,
                    })
            
            # Check raw_extracted
            extracted_dir = run_dir / "raw_extracted"
            if extracted_dir.exists():
                for f in extracted_dir.glob(f"*{rera_clean}*"):
                    file_artifacts["raw_extracted"].append({
                        "path": str(f.relative_to(OUTPUTS_BASE)),
                        "full_path": str(f),
                        "run": run_dir.name,
                        "size_bytes": f.stat().st_size if f.exists() else 0,
                    })
            
            # Check previews
            previews_dir = run_dir / "previews"
            if previews_dir.exists():
                # Previews might be in subdirectories by project
                for f in previews_dir.glob(f"**/*{rera_clean}*"):
                    file_artifacts["previews"].append({
                        "path": str(f.relative_to(OUTPUTS_BASE)),
                        "full_path": str(f),
                        "run": run_dir.name,
                        "size_bytes": f.stat().st_size if f.exists() else 0,
                    })
    
    return file_artifacts


def _get_amenity_details(project: Project) -> dict[str, Any]:
    """Get detailed amenity breakdown for debugging."""
    
    onsite = []
    nearby = []
    
    for stat in project.amenity_stats:
        stat_data = {
            "amenity_type": stat.amenity_type,
            "radius_km": float(stat.radius_km) if stat.radius_km else None,
            "nearby_count": stat.nearby_count,
            "nearby_nearest_km": float(stat.nearby_nearest_km) if stat.nearby_nearest_km else None,
            "onsite_available": stat.onsite_available,
            "onsite_details": stat.onsite_details,
            "provider_snapshot": stat.provider_snapshot,
            "last_computed_at": str(stat.last_computed_at) if stat.last_computed_at else None,
        }
        
        if stat.radius_km is None:
            onsite.append(stat_data)
        else:
            nearby.append(stat_data)
    
    return {
        "onsite": sorted(onsite, key=lambda x: x["amenity_type"]),
        "nearby": sorted(nearby, key=lambda x: (x["amenity_type"], x["radius_km"] or 0)),
    }


def _get_pricing_details(project: Project) -> dict[str, Any]:
    """Get detailed pricing snapshots for debugging."""
    
    snapshots = []
    for snapshot in project.pricing_snapshots:
        snapshots.append({
            "id": snapshot.id,
            "snapshot_date": str(snapshot.snapshot_date),
            "unit_type_label": snapshot.unit_type_label,
            "min_price_total": float(snapshot.min_price_total) if snapshot.min_price_total else None,
            "max_price_total": float(snapshot.max_price_total) if snapshot.max_price_total else None,
            "min_price_per_sqft": float(snapshot.min_price_per_sqft) if snapshot.min_price_per_sqft else None,
            "max_price_per_sqft": float(snapshot.max_price_per_sqft) if snapshot.max_price_per_sqft else None,
            "source_type": snapshot.source_type,
            "source_reference": snapshot.source_reference,
            "is_active": snapshot.is_active,
            "raw_data": snapshot.raw_data,
        })
    
    return {"snapshots": sorted(snapshots, key=lambda x: x["snapshot_date"], reverse=True)}


def _get_geo_details(project: Project) -> dict[str, Any]:
    """Get detailed geo/location information for debugging."""
    
    locations = []
    for loc in project.locations:
        locations.append({
            "id": loc.id,
            "source_type": loc.source_type,
            "lat": float(loc.lat),
            "lon": float(loc.lon),
            "precision_level": loc.precision_level,
            "confidence_score": float(loc.confidence_score) if loc.confidence_score else None,
            "is_active": loc.is_active,
            "meta_data": loc.meta_data,
            "created_at": str(loc.created_at) if loc.created_at else None,
        })
    
    return {
        "primary": {
            "lat": float(project.latitude) if project.latitude else None,
            "lon": float(project.longitude) if project.longitude else None,
            "geocoding_status": project.geocoding_status,
            "geocoding_source": project.geocoding_source,
            "geo_source": project.geo_source,
            "geo_precision": project.geo_precision,
            "geo_confidence": float(project.geo_confidence) if project.geo_confidence else None,
            "geo_normalized_address": project.geo_normalized_address,
            "geo_formatted_address": project.geo_formatted_address,
        },
        "candidate_locations": locations,
    }


def _get_score_details(project: Project) -> dict[str, Any]:
    """Get detailed score breakdown for debugging."""
    
    if not project.score:
        return {"status": "no_scores"}
    
    score = project.score
    return {
        "amenity_score": float(score.amenity_score) if score.amenity_score else None,
        "location_score": float(score.location_score) if score.location_score else None,
        "connectivity_score": score.connectivity_score,
        "daily_needs_score": score.daily_needs_score,
        "social_infra_score": score.social_infra_score,
        "overall_score": float(score.overall_score) if score.overall_score else None,
        "value_score": float(score.value_score) if score.value_score else None,
        "score_status": score.score_status,
        "score_status_reason": score.score_status_reason,
        "score_version": score.score_version,
        "last_computed_at": str(score.last_computed_at) if score.last_computed_at else None,
    }


@router.get("/projects/{project_id}/full_debug")
def get_project_full_debug(
    project_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Return comprehensive debug information for a project.
    
    This endpoint is for internal/developer use only.
    It combines:
    - Standard project detail data
    - Detailed score breakdowns
    - Full amenity stats (onsite + nearby)
    - Pricing snapshot history
    - Geo/location candidate data
    - File artifact paths (scraped JSON, HTML snapshots, previews)
    - DB artifact records
    """
    
    # Load project with all relations
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
            selectinload(Project.artifacts),
            selectinload(Project.land_parcels),
            selectinload(Project.bank_accounts),
        )
        .filter(Project.id == project_id)
        .one_or_none()
    )
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get the standard detail payload
    detail_payload = fetch_project_detail(db, project_id)
    
    # Build debug sections
    debug_payload = {
        # Core project info
        "core": {
            "id": project.id,
            "state_code": project.state_code,
            "rera_registration_number": project.rera_registration_number,
            "project_name": project.project_name,
            "status": project.status,
            "district": project.district,
            "tehsil": project.tehsil,
            "village_or_locality": project.village_or_locality,
            "full_address": project.full_address,
            "normalized_address": project.normalized_address,
            "pincode": project.pincode,
            "approved_date": str(project.approved_date) if project.approved_date else None,
            "proposed_end_date": str(project.proposed_end_date) if project.proposed_end_date else None,
            "extended_end_date": str(project.extended_end_date) if project.extended_end_date else None,
            "data_quality_score": project.data_quality_score,
            "scraped_at": str(project.scraped_at) if project.scraped_at else None,
            "last_parsed_at": str(project.last_parsed_at) if project.last_parsed_at else None,
        },
        
        # Promoter info
        "promoters": [
            {
                "name": p.promoter_name,
                "type": p.promoter_type,
                "email": p.email,
                "phone": p.phone,
                "address": p.address,
                "website": p.website,
            }
            for p in project.promoters
        ],
        
        # Standard detail payload (scores, amenities summary, pricing summary)
        "detail": detail_payload,
        
        # Detailed breakdowns for debugging
        "debug": {
            "scores_detail": _get_score_details(project),
            "geo_detail": _get_geo_details(project),
            "amenities_detail": _get_amenity_details(project),
            "pricing_detail": _get_pricing_details(project),
            "db_artifacts": _find_project_artifacts(project, db),
            "file_artifacts": _find_file_artifacts(project.rera_registration_number),
        },
        
        # Raw data JSON stored in the project record
        "raw_data_json": project.raw_data_json,
        
        # Meta
        "_meta": {
            "endpoint": "full_debug",
            "project_id": project_id,
            "rera_number": project.rera_registration_number,
            "warning": "This endpoint is for internal/developer use only",
        },
    }
    
    return debug_payload


@router.get("/projects/search_by_rera/{rera_number}")
def search_project_by_rera(
    rera_number: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Search for a project by RERA registration number.
    Returns the project ID if found, for use with the full_debug endpoint.
    """
    
    project = (
        db.query(Project)
        .filter(Project.rera_registration_number.ilike(f"%{rera_number}%"))
        .first()
    )
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "project_id": project.id,
        "rera_registration_number": project.rera_registration_number,
        "project_name": project.project_name,
        "district": project.district,
    }


__all__ = ["router"]
