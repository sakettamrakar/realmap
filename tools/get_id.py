
from cg_rera_extractor.db import get_engine, get_session_local, Project
engine = get_engine()
SessionLocal = get_session_local(engine)
with SessionLocal() as db:
    p = db.query(Project).filter(Project.rera_registration_number == "PCGRERA270418000009").first()
    if p:
        print(f"Project ID: {p.id}")
    else:
        print("Project not found.")
