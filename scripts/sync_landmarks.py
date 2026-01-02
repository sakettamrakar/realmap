"""
Synchronize project landmarks (proximity linking).
Part of Phase 2: Enhanced Geospatial Intelligence.
"""
import os
import sys
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add current directory to path
sys.path.append(os.getcwd())

from cg_rera_extractor.db.models import ProjectLocation
from cg_rera_extractor.db.models_discovery import Landmark, ProjectLandmark
from cg_rera_extractor.utils.geo_utils import Coordinates, haversine_distance

DB_URL = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"
MAX_RADIUS_KM = 10.0 # Standard proximity radius

def sync_landmarks():
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Starting landmark proximity sync...")
        
        # Get all project locations
        proj_locs = session.query(ProjectLocation).filter(ProjectLocation.is_active == True).all()
        # Get all landmarks
        landmarks = session.query(Landmark).filter(Landmark.is_active == True).all()
        
        for p_loc in proj_locs:
            p_coord = Coordinates(float(p_loc.lat), float(p_loc.lon))
            
            for lm in landmarks:
                lm_coord = Coordinates(float(lm.lat), float(lm.lon))
                
                dist = haversine_distance(p_coord, lm_coord)
                
                if dist <= MAX_RADIUS_KM:
                    # Check if link exists
                    existing = session.query(ProjectLandmark).filter_by(
                        project_id=p_loc.project_id,
                        landmark_id=lm.id
                    ).first()
                    
                    if not existing:
                        link = ProjectLandmark(
                            project_id=p_loc.project_id,
                            landmark_id=lm.id,
                            distance_km=Decimal(f"{dist:.2f}"),
                            is_highlighted=(lm.importance_score >= 90)
                        )
                        session.add(link)
                        print(f"Linked Project {p_loc.project_id} to {lm.name} ({dist:.2f} km)")
        
        session.commit()
        print("Landmark proximity sync completed.")
    except Exception as e:
        session.rollback()
        print(f"Error during sync: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    sync_landmarks()
