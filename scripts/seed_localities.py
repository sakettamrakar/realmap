"""
Seed hierarchical localities for Phase 2.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add current directory to path
sys.path.append(os.getcwd())

from cg_rera_extractor.db.models_discovery import Locality

DB_URL = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"

def seed_localities():
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Seeding hierarchical localities...")
        
        # 1. Create Parent (District)
        district = Locality(
            name="Raipur",
            slug="raipur-district",
            locality_type="DISTRICT",
            state_code="CG"
        )
        session.add(district)
        session.flush()
        
        # 2. Create Children (Tehsils/Areas)
        localities = [
            {"name": "Labhandi", "slug": "labhandi", "type": "LOCALITY", "parent_id": district.id},
            {"name": "Telibandha", "slug": "telibandha", "type": "LOCALITY", "parent_id": district.id},
            {"name": "Mowa", "slug": "mowa", "type": "LOCALITY", "parent_id": district.id}
        ]
        
        for loc_data in localities:
            loc = Locality(
                name=loc_data["name"],
                slug=loc_data["slug"],
                locality_type=loc_data["type"],
                parent_locality_id=loc_data["parent_id"],
                state_code="CG"
            )
            session.add(loc)
            print(f"Added Locality: {loc_data['name']}")
        
        session.commit()
        print("Locality seeding completed.")
    except Exception as e:
        session.rollback()
        print(f"Error seeding localities: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_localities()
