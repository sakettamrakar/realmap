
import sys
import psycopg2

# Get DATABASE_URL from .env or argument
# Since we might not have python-dotenv installed, let's parse .env manually or use the one provided
env_db_url = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"

# Or try to read .env
try:
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                env_db_url = line.strip().split("=", 1)[1]
                break
except FileNotFoundError:
    pass

print(f"Testing connection to: {env_db_url}")

try:
    conn = psycopg2.connect(env_db_url)
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    result = cur.fetchone()
    print(f"Connection successful! Result: {result[0]}")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
