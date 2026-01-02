
import logging
from pathlib import Path
from cg_rera_extractor.db import get_engine, get_session_local, Base
from cg_rera_extractor.db.loader import _load_project
from cg_rera_extractor.parsing.schema import V1Project
from cg_rera_extractor.parsing.raw_extractor import extract_raw_from_html
from cg_rera_extractor.parsing.mapper import map_raw_to_v1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shredder")

def main():
    engine = get_engine()
    # Ensure Unit table exists
    Base.metadata.create_all(bind=engine)
    
    base_output = Path(r"c:\GIT\realmap\outputs")
    # We find all HTML files to re-extract high-res data
    html_files = list(base_output.rglob("*.html"))
    print(f"Found {len(html_files)} HTML files for high-res extraction.")
    
    SessionLocal = get_session_local(engine)
    total_units = 0
    total_projects = 0
    
    for i, html_file in enumerate(html_files):
        if i % 20 == 0:
            print(f"Progress: {i}/{len(html_files)}...")
            
        try:
            # 1. Extract Raw (Freshly from HTML with new Table Mode)
            # Filename format: project_CG_PCGRERA...html
            project_key = html_file.stem.replace("project_", "", 1)
            reg_no = None
            if project_key.startswith("CG_"):
                reg_no = project_key[len("CG_"):]
            
            html_content = html_file.read_text(encoding="utf-8")
            raw = extract_raw_from_html(
                html_content, 
                source_file=str(html_file),
                registration_number=reg_no
            )
            
            # 2. Map to V1
            v1_project = map_raw_to_v1(raw, state_code="CG")
            
            # 3. Load into DB (Shredding happens inside _load_project)
            with SessionLocal() as session:
                stats = _load_project(session, v1_project)
                session.commit()
                total_units += stats.units
                total_projects += stats.projects_upserted
        except Exception as e:
            # logger.error(f"Failed to process {html_file.name}: {e}")
            pass
                
    print(f"\nSHREDDING COMPLETE!")
    print(f"Total Projects Impacted: {total_projects}")
    print(f"Total Units Shredded:    {total_units}")

if __name__ == "__main__":
    main()
