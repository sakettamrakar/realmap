
import sys
import psycopg2

env_db_url = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"
# Try load from .env
try:
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                env_db_url = line.strip().split("=", 1)[1]
                break
except:
    pass

required_tables = ["projects", "ai_scores"]
required_columns = {
    "ai_scores": ["score_value", "confidence", "model_name", "created_at", "input_features", "explanation"]
}

try:
    conn = psycopg2.connect(env_db_url)
    cur = conn.cursor()
    
    # Check tables
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables = [row[0] for row in cur.fetchall()]
    print(f"Found tables: {tables}")
    
    missing_tables = [t for t in required_tables if t not in tables]
    if missing_tables:
        print(f"Missing tables: {missing_tables}")
        sys.exit(1)
        
    # Check columns
    for table, cols in required_columns.items():
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}';")
        existing_cols = [row[0] for row in cur.fetchall()]
        missing_cols = [c for c in cols if c not in existing_cols]
        if missing_cols:
            print(f"Missing columns in {table}: {missing_cols}")
            sys.exit(1)
            
    print("Schema verification passed!")
    conn.close()
except Exception as e:
    print(f"Schema verification failed: {e}")
    sys.exit(1)
