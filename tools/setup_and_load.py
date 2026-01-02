from cg_rera_extractor.db.init_db import init_db
from cg_rera_extractor.db.loader import load_run_into_db
from cg_rera_extractor.db import Base, get_engine
from cg_rera_extractor.config.env import ensure_database_url
from pathlib import Path
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("setup_load")

def main():
    print("\n" + "="*80)
    print("REALMAP DATA LOADER")
    print("="*80 + "\n")

    # 1. Initialize DB Schema
    logger.info("Step 1/2: Syncing Database Schema (Units only fresh)...")
    try:
        engine = get_engine()
        # Drop units table to ensure fresh schema
        from cg_rera_extractor.db import Base
        print("Dropping 'units' table for a fresh start...")
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS units CASCADE"))
                conn.commit()
        except:
            pass
            
        Base.metadata.create_all(bind=engine)
        logger.info("Schema synced (tables created if missing).")
    except Exception as e:
        logger.warning(f"Schema sync warning (might already be fine): {e}")

    # 2. Load Runs
    logger.info("Step 2/2: Loading scraped data from 'outputs'...")
    base_output = Path(r"c:\GIT\realmap\outputs")
    
    # Find all 'run_*' directories that contain 'scraped_json'
    # Use rglob with a more flexible search
    candidates = []
    # We walk the entire outputs tree to find directories starting with run_
    for run_dir in base_output.rglob("run_*"):
        if run_dir.is_dir() and (run_dir / "scraped_json").exists():
            candidates.append(run_dir)
    
    # Sort by name for consistency
    candidates.sort(key=lambda x: x.name)
    
    # Remove duplicates if any (though run IDs should be unique)
    seen_runs = set()
    unique_candidates = []
    for c in candidates:
        if c.name not in seen_runs:
            unique_candidates.append(c)
            seen_runs.add(c.name)
    
    print(f"\nFound {len(unique_candidates)} unique runs to process.")
    
    total_units_loaded = 0
    total_projects = 0
    
    for i, run_dir in enumerate(unique_candidates):
        print(f"\n[{i+1}/{len(unique_candidates)}] Processing {run_dir}...")
        try:
            stats = load_run_into_db(str(run_dir))
            u_count = stats.get('units', 0)
            p_count = stats.get('projects_upserted', 0)
            
            total_units_loaded += u_count
            total_projects += p_count
            
            print(f"  -> +{p_count} Projects, +{u_count} Units")
        except Exception as e:
            logger.error(f"  -> Failed to load {run_dir}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("LOAD COMPLETE")
    print(f"Total Projects Processed: {total_projects}")
    print(f"Total Units Shredded:     {total_units_loaded}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
