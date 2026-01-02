
import logging
import os
import sys
from pathlib import Path
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from cg_rera_extractor.parsing.mapper import map_raw_to_v1
from cg_rera_extractor.parsing.raw_extractor import extract_raw_from_html
from cg_rera_extractor.db.loader import load_run_into_db, get_session_local, get_engine
from cg_rera_extractor.db.models import IngestionAudit
from sqlalchemy import delete

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("reprocess_all.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def reparse_run(run_dir: Path):
    """Reparse all HTML files in a run and save to scraped_json."""
    raw_html_dir = run_dir / "raw_html"
    scraped_json_dir = run_dir / "scraped_json"
    
    if not raw_html_dir.exists():
        logger.warning(f"No raw_html directory in {run_dir}")
        return False
    
    scraped_json_dir.mkdir(parents=True, exist_ok=True)
    
    html_files = list(raw_html_dir.glob("*.html")) + list(raw_html_dir.glob("*.htm"))
    if not html_files:
        logger.warning(f"No HTML files in {raw_html_dir}")
        return False
    
    logger.info(f"Reparsing {len(html_files)} files in {run_dir.name}...")
    
    success_count = 0
    for html_file in html_files:
        try:
            html_content = html_file.read_text(encoding="utf-8")
            
            # Extract registration number from filename if possible (e.g. project_CG_1.html)
            reg_no = None
            if "_" in html_file.stem:
                parts = html_file.stem.split("_")
                if len(parts) >= 3:
                    reg_no = "_".join(parts[1:])
            
            raw = extract_raw_from_html(
                html_content,
                source_file=str(html_file),
                registration_number=reg_no
            )
            
            v1_project = map_raw_to_v1(raw, state_code="CG")
            
            # Save to scraped_json
            output_path = scraped_json_dir / f"{html_file.stem}.v1.json"
            output_path.write_text(
                v1_project.model_dump_json(indent=2, exclude_none=True),
                encoding="utf-8"
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to parse {html_file.name}: {e}")
            
    logger.info(f"Successfully reparsed {success_count}/{len(html_files)} files in {run_dir.name}")
    return success_count > 0

def main():
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        logger.error("Outputs directory not found")
        return
    
    # Find all run_* directories
    run_dirs = []
    for root, dirs, files in os.walk(outputs_dir):
        for d in dirs:
            if d.startswith("run_"):
                run_dirs.append(Path(root) / d)
    
    logger.info(f"Found {len(run_dirs)} run directories to reprocess")
    
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    session = SessionLocal()
    
    total_stats = {
        "runs_processed": 0,
        "projects_upserted": 0,
        "failed_runs": 0
    }
    
    try:
        for run_dir in sorted(run_dirs):
            logger.info(f"Processing run: {run_dir}")
            
            # 1. Reparse
            if reparse_run(run_dir):
                # 2. Load into DB
                try:
                    # Clear existing audit to avoid UniqueViolation
                    session.execute(delete(IngestionAudit).where(IngestionAudit.run_id == run_dir.name))
                    session.flush()
                    
                    stats = load_run_into_db(str(run_dir), session=session)
                    total_stats["projects_upserted"] += stats.get("projects_upserted", 0)
                    total_stats["runs_processed"] += 1
                    logger.info(f"Loaded run {run_dir.name}: {stats}")
                    # Commit after each run to save progress
                    session.commit()
                except Exception as e:
                    logger.error(f"Failed to load run {run_dir.name} into DB: {e}")
                    session.rollback()
                    total_stats["failed_runs"] += 1
            else:
                logger.warning(f"Skipping load for {run_dir.name} due to reparse failure or no data")
                total_stats["failed_runs"] += 1
                
    finally:
        session.close()
        
    logger.info("="*60)
    logger.info("REPROCESS COMPLETE")
    logger.info(f"Total runs processed: {total_stats['runs_processed']}")
    logger.info(f"Total projects upserted: {total_stats['projects_upserted']}")
    logger.info(f"Total failed runs: {total_stats['failed_runs']}")
    logger.info("="*60)

if __name__ == "__main__":
    main()
