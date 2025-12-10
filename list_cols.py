
import psycopg2
env_db_url = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"
try:
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                env_db_url = line.strip().split("=", 1)[1]
                break
except: pass

conn = psycopg2.connect(env_db_url)
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='projects';")
print([row[0] for row in cur.fetchall()])
conn.close()
