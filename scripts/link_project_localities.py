"""
Link projects to locality IDs based on seed data.
Part of Phase 2: Enhanced Geospatial Intelligence.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add current directory to path
sys.path.append(os.getcwd())

from cg_rera_extractor.db.models import Project
from cg_rera_extractor.db.models_discovery import Locality

DB_URL = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"

def link_localities():
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Linking projects to localities...")
        
        # Mapping for test projects
        links = {
            2: "labhandi", # GT LIFE SPACES
            1: "mowa"      # Project 1
        }
        
        for pid, slug in links.items():
            loc = session.query(Locality).filter_by(slug=slug).first()
            if loc:
                proj = session.query(Project).get(pid)
                if proj:
                    proj.locality_id = loc.id
                    print(f"Linked Project {pid} to Locality {loc.name}")
        
        session.commit()
        print("Locality linking completed.")
    except Exception as e:
        session.rollback()
        print(f"Error linking localities: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    link_localities()
