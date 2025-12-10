"""Apply V002 migration."""
from sqlalchemy import text
from cg_rera_extractor.db import get_engine
from pathlib import Path

def apply_migration():
    """Read and execute V002_add_ai_scores.sql."""
    engine = get_engine()
    
    migration_file = Path(__file__).parent / "V002_add_ai_scores.sql"
    if not migration_file.exists():
        print(f"Error: {migration_file} not found")
        return

    sql_content = migration_file.read_text(encoding="utf-8")
    
    print(f"Applying migration from {migration_file.name}...")
    
    with engine.connect() as conn:
        try:
            # Execute the whole block. The SQL file has BEGIN/COMMIT, 
            # but SQLAlchemy also manages transactions. 
            # We'll rely on the SQL file's transaction control or just execute.
            # Splitting by statement is safer if the driver doesn't support multistatement.
            # However, for simple DDL, executing as one block often works or fails.
            # Let's try executing as one block first.
            conn.execute(text(sql_content))
            conn.commit()
            print("✓ Migration applied successfully.")
        except Exception as e:
            print(f"✗ Error applying migration: {e}")

if __name__ == "__main__":
    apply_migration()
