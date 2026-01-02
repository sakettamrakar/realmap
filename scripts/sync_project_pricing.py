"""
Sync project pricing snapshots from unit type data.
Part of Phase 1: Core Data Parity.
"""
import os
import sys
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Add current directory to path
sys.path.append(os.getcwd())

from cg_rera_extractor.db.models import Project, ProjectUnitType, ProjectPricingSnapshot

DB_URL = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"

def sync_pricing():
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Starting pricing synchronization...")
        
        # Get all projects
        projects = session.query(Project).all()
        
        for proj in projects:
            # Query unit types with pricing
            unit_types = session.query(ProjectUnitType).filter(
                ProjectUnitType.project_id == proj.id,
                ProjectUnitType.base_price_inr.isnot(None)
            ).all()
            
            if not unit_types:
                continue
                
            # Aggregate stats
            prices = [u.base_price_inr for u in unit_types]
            sqft_prices = [u.price_per_sqft_carpet for u in unit_types if u.price_per_sqft_carpet]
            
            min_p = min(prices)
            max_p = max(prices)
            min_sqft = min(sqft_prices) if sqft_prices else None
            max_sqft = max(sqft_prices) if sqft_prices else None
            
            # Create snapshot (dated today)
            snapshot = ProjectPricingSnapshot(
                project_id=proj.id,
                snapshot_date=date.today(),
                min_price_total=min_p,
                max_price_total=max_p,
                min_price_per_sqft=min_sqft,
                max_price_per_sqft=max_sqft,
                source_type="SYSTEM_SYNC_V1"
            )
            session.add(snapshot)
            print(f"Synced mapping for {proj.project_name}: {min_p} - {max_p}")
            
        session.commit()
        print("Pricing synchronization completed.")
    except Exception as e:
        session.rollback()
        print(f"Error during sync: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    sync_pricing()
