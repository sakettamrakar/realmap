"""
Seed sample landmarks for Phase 2 Geospatial Intelligence.
"""
import os
import sys
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add current directory to path
sys.path.append(os.getcwd())

from cg_rera_extractor.db.models_discovery import Landmark

DB_URL = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"

# Sample landmarks in Raipur, Chhattisgarh (Approximate coords)
SAMPLE_LANDMARKS = [
    {
        "slug": "magneto-mall-raipur",
        "name": "Magneto The Mall",
        "category": "MALL",
        "lat": 21.2422,
        "lon": 81.7042,
        "importance_score": 90
    },
    {
        "slug": "aiims-raipur",
        "name": "AIIMS Raipur",
        "category": "HOSPITAL",
        "lat": 21.2573,
        "lon": 81.5794,
        "importance_score": 95
    },
    {
        "slug": "nandan-van-zoo",
        "name": "Nandan Van Zoo",
        "category": "PARK",
        "lat": 21.2031,
        "lon": 81.5367,
        "importance_score": 80
    },
    {
        "slug": "ambuja-mall-raipur",
        "name": "Ambuja City Center Mall",
        "category": "MALL",
        "lat": 21.2664,
        "lon": 81.6853,
        "importance_score": 85
    }
]

def seed_landmarks():
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Seeding sample landmarks...")
        for data in SAMPLE_LANDMARKS:
            existing = session.query(Landmark).filter_by(slug=data["slug"]).first()
            if not existing:
                landmark = Landmark(
                    slug=data["slug"],
                    name=data["name"],
                    category=data["category"],
                    lat=Decimal(str(data["lat"])),
                    lon=Decimal(str(data["lon"])),
                    importance_score=data["importance_score"]
                )
                session.add(landmark)
                print(f"Added Landmark: {data['name']}")
        
        session.commit()
        print("Landmark seeding completed.")
    except Exception as e:
        session.rollback()
        print(f"Error seeding landmarks: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_landmarks()
