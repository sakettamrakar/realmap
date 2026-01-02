
from pathlib import Path
import json
import logging
from cg_rera_extractor.parsing.raw_extractor import extract_raw_from_html
from cg_rera_extractor.parsing.mapper import map_raw_to_v1
from cg_rera_extractor.db.loader import _load_project
from cg_rera_extractor.db import get_engine, get_session_local, Base

logging.basicConfig(level=logging.INFO)

def main():
    reg_no = "PCGRERA270418000009"
    html_file = Path(r"c:\GIT\realmap\outputs\raipur-20\runs\run_20251210_090333_f88ae6\raw_html\project_CG_PCGRERA270418000009.html")
    
    if not html_file.exists():
        print(f"Error: HTML file not found: {html_file}")
        return

    print(f"Processing {reg_no}...")
    html = html_file.read_text(encoding="utf-8")
    
    # 1. Extract Raw (with Table Mode)
    raw = extract_raw_from_html(html, source_file=str(html_file), registration_number=reg_no)
    
    has_tables = any(s.tables for s in raw.sections)
    print(f"Raw Extraction Complete. Tables found: {has_tables}")
    if not has_tables:
        print("Warning: No tables found in raw extraction. Check raw_extractor.py logic.")

    # 2. Map to V1
    v1_project = map_raw_to_v1(raw, state_code="CG")
    
    # 3. Load into DB
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    SessionLocal = get_session_local(engine)
    
    with SessionLocal() as session:
        print("Loading into DB...")
        stats = _load_project(session, v1_project)
        session.commit()
        print(f"Load Complete. Stats: {stats.to_dict()}")

if __name__ == "__main__":
    main()
