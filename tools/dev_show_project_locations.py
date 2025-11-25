"""Dev tool to inspect locations for a specific project."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add tools directory to path to import sibling modules
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
from cg_rera_extractor.db import Project, ProjectLocation, get_engine, get_session_local


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect locations for a project")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--project-id", type=int, help="Project ID")
    group.add_argument("--reg-number", type=str, help="RERA Registration Number")
    
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    db_url = ensure_database_url()
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    logging.info("Connected to %s", describe_database_target(db_url))

    with SessionLocal() as session:
        stmt = select(Project).options(joinedload(Project.locations))
        if args.project_id:
            stmt = stmt.where(Project.id == args.project_id)
        else:
            stmt = stmt.where(Project.rera_registration_number == args.reg_number)
            
        project = session.scalars(stmt).unique().first()
        
        if not project:
            logging.error("Project not found")
            return 1

        print(f"\n=== Project {project.id}: {project.project_name} ===")
        print(f"Registration: {project.rera_registration_number}")
        print(f"Address: {project.full_address}")
        print(f"Normalized: {project.normalized_address}")
        print("\n--- Current Canonical Pin ---")
        print(f"Lat/Lon: {project.latitude}, {project.longitude}")
        print(f"Source: {project.geo_source}")
        print(f"Precision: {project.geo_precision}")
        print(f"Confidence: {project.geo_confidence}")
        print(f"Formatted: {project.geo_formatted_address}")
        
        print("\n--- Project Locations (Candidates) ---")
        if not project.locations:
            print("No locations found.")
        else:
            # Sort by created_at desc
            locs = sorted(project.locations, key=lambda x: x.created_at or x.updated_at or datetime.min, reverse=True)
            for loc in locs:
                active_mark = "[ACTIVE]" if loc.is_active else "[INACTIVE]"
                print(f"{active_mark} ID: {loc.id} | Source: {loc.source_type}")
                print(f"  Lat/Lon: {loc.lat}, {loc.lon}")
                print(f"  Precision: {loc.precision_level} | Conf: {loc.confidence_score}")
                print(f"  Created: {loc.created_at}")
                if loc.meta_data:
                    print(f"  Meta: {loc.meta_data}")
                print("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
