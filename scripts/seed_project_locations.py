"""
Seed sample project locations for Phase 2 test.
"""
import os
import sys
from decimal import Decimal
from sqlalchemy import create_engine, text

# Add current directory to path
sys.path.append(os.getcwd())

DB_URL = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"

PROJECT_LOCS = [
    {
        "project_id": 2, # GT LIFE SPACES
        "lat": 21.2400,
        "lon": 81.7000,
        "source_type": "TEST_SEED"
    },
    {
        "project_id": 1, 
        "lat": 21.2600,
        "lon": 81.6800,
        "source_type": "TEST_SEED"
    }
]

def seed_project_locs():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        with conn.begin():
            for loc in PROJECT_LOCS:
                # Check if exists in project_locations
                exists = conn.execute(text("SELECT id FROM project_locations WHERE project_id = :pid"), {"pid": loc["project_id"]}).fetchone()
                if not exists:
                    conn.execute(text("""
                        INSERT INTO project_locations (project_id, lat, lon, source_type, is_active, created_at)
                        VALUES (:pid, :lat, :lon, :src, true, now())
                    """), {"pid": loc["project_id"], "lat": loc["lat"], "lon": loc["lon"], "src": loc["source_type"]})
                    print(f"Added location for Project ID {loc['project_id']}")
        print("Project local seeding completed.")

if __name__ == "__main__":
    seed_project_locs()
