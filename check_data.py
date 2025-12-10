
import psycopg2

env_db_url = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"
try:
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                env_db_url = line.strip().split("=", 1)[1]
                break
except:
    pass

try:
    conn = psycopg2.connect(env_db_url)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM projects;")
    count = cur.fetchone()[0]
    print(f"Projects count: {count}")
    
    if count > 0:
        cur.execute("SELECT id, project_name, status, district FROM projects LIMIT 1;")
        row = cur.fetchone()
        print(f"Sample project: {row}")
    else:
        print("No projects found in DB.")
        
    conn.close()
except Exception as e:
    print(f"DB check failed: {e}")
