import sys
from sqlalchemy import text
from cg_rera_extractor.db import get_engine

def inspect_db():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            print("Connected to DB.")
            
            # List tables
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            print(f"Tables: {tables}")
            
            for table in tables:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"\nTable: {table}, Count: {count}")
                
                if count > 0:
                    # Sample a row
                    row = conn.execute(text(f"SELECT * FROM {table} LIMIT 1")).mappings().one()
                    print(f"  Sample row keys: {list(row.keys())}")
                    print(f"  Sample row values: {dict(row)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Redirect stdout to a file
    with open('db_inspection.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        inspect_db()
