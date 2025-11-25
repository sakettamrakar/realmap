"""Debug script to investigate geocoding failures."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from sqlalchemy import select

from cg_rera_extractor.config.env import ensure_database_url
from cg_rera_extractor.config.models import GeocoderConfig
from cg_rera_extractor.db import Project, get_engine, get_session_local
from cg_rera_extractor.geo.geocoder import build_geocoding_client

# Configure logging to see debug output
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

def main() -> None:
    ensure_database_url()
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    
    # Use default config (Nominatim)
    config = GeocoderConfig()
    client = build_geocoding_client(config)
    
    with SessionLocal() as session:
        # Fetch the failed projects
        stmt = select(Project).where(Project.geocoding_status == 'FAILED')
        projects = session.scalars(stmt).all()
        
        print(f"Found {len(projects)} failed projects.")
        
        for project in projects:
            print(f"\n--- Debugging Project {project.id} ---")
            print(f"Reg Number: {project.rera_registration_number}")
            print(f"Normalized Address: '{project.normalized_address}'")
            
            if not project.normalized_address:
                print("ERROR: Normalized address is empty!")
                continue
                
            print("Attempting to geocode...")
            result = client.geocode(project.normalized_address)
            
            if result:
                print("SUCCESS!")
                print(f"Lat: {result.lat}, Lon: {result.lon}")
                print(f"Formatted: {result.formatted_address}")
                print(f"Source: {result.geo_source}")
            else:
                print("FAILURE: Geocoder returned None.")
                
            # Also try a known good address to verify connectivity
            print("\n--- Connectivity Check ---")
            test_addr = "Raipur, Chhattisgarh, India"
            print(f"Geocoding '{test_addr}'...")
            result = client.geocode(test_addr)
            if result:
                print(f"Connectivity OK. Result: {result.lat}, {result.lon}")
            else:
                print("Connectivity Check FAILED.")
                
            # Break after first project to avoid spamming
            break

if __name__ == "__main__":
    main()
