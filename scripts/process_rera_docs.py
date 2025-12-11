"""
CLI Script to batch process RERA PDF documents.
Usage:
    python scripts/process_rera_docs.py --input-dir "data/raw_pdfs"
"""
import argparse
import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in path
sys.path.append(os.getcwd())

from ai.rera.parser import ReraPdfParser
from cg_rera_extractor.db.models import Project
from cg_rera_extractor.config.loader import load_config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Batch process RERA PDFs")
    parser.add_argument("--input-dir", required=True, help="Directory containing PDF files")
    parser.add_argument("--project-id", type=int, help="Optional Project ID to associate with (if processing single folder for a project)")
    
    args = parser.parse_args()
    
    # 1. Load Config & DB
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        # Fallback to example if dev env
        config_path = "config.example.yaml"
        
    app_config = load_config(config_path)
    db_url = app_config.db.url
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # 2. Initialize Parser
    pdf_parser = ReraPdfParser(use_ocr=True)
    
    # 3. Iterate
    if not os.path.exists(args.input_dir):
        logger.error(f"Input directory not found: {args.input_dir}")
        return
        
    files = [f for f in os.listdir(args.input_dir) if f.lower().endswith('.pdf')]
    logger.info(f"Found {len(files)} PDFs in {args.input_dir}")
    
    for filename in files:
        file_path = os.path.join(args.input_dir, filename)
        logger.info(f"Processing {filename}...")
        
        try:
            # If project_id is not provided, we might try to infer it or just use a default/null if model allows
            # But our model requires project_id. 
            # For this prototype, we require project_id in args or skip.
            # Real implementation might parse project ID from filename or folder structure.
            
            target_project_id = args.project_id
            if not target_project_id:
                # Try to find *any* project to attach to for testing, or fail
                # For safety, let's just use the first project in DB if not specified (ONLY FOR DEV)
                first_api = db.query(Project).first()
                if first_api:
                    target_project_id = first_api.id
                else:
                    logger.error("No projects in DB to attach file to.")
                    continue
            
            result = pdf_parser.process_file(file_path, project_id=target_project_id, db=db)
            logger.info(f"Success! Filing ID: {result['filing_id']}")
            
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")
            
    db.close()
    logger.info("Batch processing complete.")

if __name__ == "__main__":
    main()
