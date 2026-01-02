import sys
import os
from sqlalchemy import create_engine, inspect, text

# Add current directory to path
sys.path.append(os.getcwd())

DB_URL = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"

def check_tables():
    engine = create_engine(DB_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Existing tables:")
    for table in sorted(tables):
        print(f"- {table}")
    
    with engine.connect() as conn:
        try:
            res = conn.execute(text("SELECT version_num FROM alembic_version"))
            versions = res.fetchall()
            print("\nAlembic heads in DB:")
            for v in versions:
                print(f"- {v[0]}")
        except Exception:
            print("\nalembic_version table not found or error reading it.")

if __name__ == "__main__":
    check_tables()
