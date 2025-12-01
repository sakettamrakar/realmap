import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from cg_rera_extractor.db.init_db import init_db

if __name__ == "__main__":
    print("Initializing database...")
    init_db(run_migrations=True) # Run migrations to update schema
    print("Database initialized.")
