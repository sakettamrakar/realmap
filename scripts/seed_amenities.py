"""
Seed the database with a standardized amenity taxonomy.
Part of Phase 1: Core Data Parity.
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add current directory to path to allow imports
sys.path.append(os.getcwd())

from cg_rera_extractor.db.models_enhanced import AmenityCategory, Amenity, AmenityType
from cg_rera_extractor.db.enums import AmenityCategoryType

# Database connection
# In production, use environment variables
DB_URL = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"

AMENITY_TAXONOMY = {
    AmenityCategoryType.HEALTH: {
        "name": "Health & Wellness",
        "weight": 10.0,
        "amenities": [
            {"code": "gym", "name": "Gymnasium", "points": 10},
            {"code": "yoga", "name": "Yoga/Meditation Area", "points": 8},
            {"code": "spa", "name": "Spa & Sauna", "points": 12},
            {"code": "clinic", "name": "Medical Center", "points": 15},
        ]
    },
    AmenityCategoryType.LEISURE: {
        "name": "Leisure & Sports",
        "weight": 8.0,
        "amenities": [
            {"code": "pool", "name": "Swimming Pool", "points": 15},
            {"code": "club", "name": "Clubhouse", "points": 20},
            {"code": "theater", "name": "Mini Theater", "points": 10},
            {"code": "badminton", "name": "Badminton Court", "points": 8},
            {"code": "cricket", "name": "Cricket Pitch", "points": 5},
        ]
    },
    AmenityCategoryType.SECURITY: {
        "name": "Security & Safety",
        "weight": 10.0,
        "amenities": [
            {"code": "cctv", "name": "24/7 CCTV", "points": 15},
            {"code": "intercom", "name": "Intercom Facility", "points": 5},
            {"code": "fire", "name": "Fire Fighting System", "points": 20},
            {"code": "gated", "name": "Gated Community", "points": 25},
        ]
    },
    AmenityCategoryType.ENVIRONMENT: {
        "name": "Environment & Greenery",
        "weight": 9.0,
        "amenities": [
            {"code": "park", "name": "Park / Garden", "points": 12},
            {"code": "rwh", "name": "Rain Water Harvesting", "points": 15},
            {"code": "solar", "name": "Solar Water Heating", "points": 18},
            {"code": "stp", "name": "Sewage Treatment Plant", "points": 20},
        ]
    },
    AmenityCategoryType.CONVENIENCE: {
        "name": "Convenience & Services",
        "weight": 7.0,
        "amenities": [
            {"code": "lift", "name": "High Speed Lifts", "points": 10},
            {"code": "power", "name": "Power Backup", "points": 25},
            {"code": "wifi", "name": "Fiber Internet", "points": 8},
            {"code": "parking", "name": "Reserved Parking", "points": 15},
        ]
    }
}

def seed_taxonomy():
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Starting amenity taxonomy seeding...")
        
        for cat_enum, data in AMENITY_TAXONOMY.items():
            # Create or update category
            category = session.query(AmenityCategory).filter_by(code=cat_enum.value).first()
            if not category:
                category = AmenityCategory(
                    code=cat_enum.value,
                    name=data["name"],
                    lifestyle_weight=data["weight"]
                )
                session.add(category)
                session.flush() # Get the ID
                print(f"Added Category: {data['name']}")
            
            for am_data in data["amenities"]:
                amenity = session.query(Amenity).filter_by(code=am_data["code"]).first()
                if not amenity:
                    amenity = Amenity(
                        category_id=category.id,
                        code=am_data["code"],
                        name=am_data["name"],
                        lifestyle_points=am_data["points"]
                    )
                    session.add(amenity)
                    print(f"  Added Amenity: {am_data['name']}")
        
        session.commit()
        print("Seeding completed successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error during seeding: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_taxonomy()
