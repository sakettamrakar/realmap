
import logging
from pathlib import Path
from cg_rera_extractor.db import get_engine, get_session_local, Base
from cg_rera_extractor.db.loader import _load_project
from cg_rera_extractor.parsing.schema import V1Project

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("force_loader")

def main():
    engine = get_engine()
    # Ensure Unit table exists
    Base.metadata.create_all(bind=engine)
    
    base_output = Path(r"c:\GIT\realmap\outputs")
    v1_files = list(base_output.rglob("*.v1.json"))
    print(f"Found {len(v1_files)} V1 JSON files.")
    
    SessionLocal = get_session_local(engine)
    total_units = 0
    total_projects = 0
    
    for i, path in enumerate(v1_files):
        if i % 10 == 0:
            print(f"Processing {i}/{len(v1_files)}...")
            
        with SessionLocal() as session:
            try:
                json_text = path.read_text(encoding='utf-8-sig')
                v1_project = V1Project.model_validate_json(json_text)
                
                # We call the internal _load_project which now includes units
                stats = _load_project(session, v1_project)
                
                session.commit()
                total_units += stats.units
                total_projects += stats.projects_upserted
            except Exception as e:
                # logger.error(f"Failed {path.name}: {e}")
                session.rollback()
                
    print(f"COMPLETE! Projects: {total_projects}, Units: {total_units}")

if __name__ == "__main__":
    main()
