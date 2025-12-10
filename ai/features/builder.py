from sqlalchemy.orm import Session
from cg_rera_extractor.db import get_session_local
from cg_rera_extractor.db.models import Project
from ai.schemas import FeatureSnapshot

def build_feature_pack(project_id: int, db: Session = None) -> FeatureSnapshot:
    """
    Constructs a JSON-serializable feature pack for a project.
    If db session is not provided, creates a new one.
    """
    close_db = False
    if db is None:
        db = get_session_local()
        close_db = True
        
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
            
        # Basic details
        features = {
            "id": project.id,
            "name": project.project_name,
            "state": project.state_code,
            "city": project.district,
            "tehsil": project.tehsil,
            "status": project.status,
            "approved_date": str(project.approved_date) if project.approved_date else None,
            "proposed_end_date": str(project.proposed_end_date) if project.proposed_end_date else None,
            "area": float(project.open_space_area_sqmt) if project.open_space_area_sqmt else None,
            "type": "Residential", # TODO: Infer from data
        }
        
        # Promoters
        promoters = []
        for p in project.promoters:
            promoters.append({
                "name": p.promoter_name,
                "type": p.promoter_type
            })
        features["promoters"] = promoters
        
        # Amenities (Available vs Context)
        amenities_onsite = []
        amenities_nearby = []
        
        for stat in project.amenity_stats:
            if stat.onsite_available:
                amenities_onsite.append(stat.amenity_type)
            if stat.nearby_count and stat.nearby_count > 0:
                amenities_nearby.append({
                    "type": stat.amenity_type,
                    "count": stat.nearby_count,
                    "nearest_km": float(stat.nearby_nearest_km) if stat.nearby_nearest_km else None
                })
                
        features["amenities"] = {
            "onsite": amenities_onsite,
            "nearby": amenities_nearby
        }
        
        # Completeness signals
        features["signals"] = {
            "has_lat_lon": bool(project.latitude and project.longitude),
            "has_documents": len(project.documents) > 0,
            "has_quarterly_updates": len(project.quarterly_updates) > 0
        }
        
        return FeatureSnapshot(project_id=project_id, features=features)
        
    finally:
        if close_db:
            db.close()
