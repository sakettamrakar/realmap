"""Fix database schema by adding missing columns."""
from __future__ import annotations

from sqlalchemy import text

from cg_rera_extractor.config.env import ensure_database_url
from cg_rera_extractor.db import get_engine

def main() -> None:
    ensure_database_url()
    engine = get_engine()
    
    with engine.connect() as conn:
        print("Checking for normalized_address column...")
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='projects' AND column_name='normalized_address'"
        ))
        if not result.scalar():
            print("Adding normalized_address column...")
            conn.execute(text("ALTER TABLE projects ADD COLUMN normalized_address VARCHAR(512)"))
            conn.commit()
            print("Column added.")
        else:
            print("Column already exists.")
            
        # Also check for formatted_address if needed (geocode_projects uses it)
        print("Checking for formatted_address column...")
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='projects' AND column_name='formatted_address'"
        ))
        if not result.scalar():
            print("Adding formatted_address column...")
            conn.execute(text("ALTER TABLE projects ADD COLUMN formatted_address VARCHAR(512)"))
            conn.commit()
            print("Column added.")
        else:
            print("Column already exists.")

if __name__ == "__main__":
    main()
