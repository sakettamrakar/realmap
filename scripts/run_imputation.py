#!/usr/bin/env python3
"""
CLI script to run AI imputation for missing project data.

Usage:
    python scripts/run_imputation.py --limit 100 --dry-run
"""
import argparse
import logging
import sys
from sqlalchemy import select, or_

from cg_rera_extractor.db.base import get_engine, get_session_local
from cg_rera_extractor.db.models import Project
from ai.imputation.engine import ImputationEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("run_imputation")

def run_imputation(limit: int = 100, dry_run: bool = False):
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    session = SessionLocal()
    
    try:
        imputer = ImputationEngine(session)
        
        # 1. Train Model
        logger.info("Step 1: Training Model...")
        imputer.train()
        
        if not imputer.is_trained:
            logger.error("Model failed to train (insufficient data). Exiting.")
            sys.exit(1)
            
        # 2. Identify Candidates
        logger.info("Step 2: Identifying projects with missing data...")
        stmt = select(Project).where(
            or_(
                Project.proposed_end_date.is_(None),
                # If checking total_units is costly via relationship in query, 
                # we iterate. For now, let's keep it simple and just iterate logic.
                # Just get latest projects
            )
        ).limit(limit)
        
        # Note: A better query would join buildings/unit_types to find nulls.
        # For simplicity, we grab recent projects and check in python.
        stmt = select(Project).order_by(Project.id.desc()).limit(limit)
        
        projects = session.scalars(stmt).all()
        logger.info(f"Scanning {len(projects)} recent projects check for gaps...")
        
        metrics = {"processed": 0, "imputed": 0}
        
        for p in projects:
            # Check if needs imputation
            # (Logic simplified: if engine returns non-empty dict, it means it found gaps)
            try:
                prediction = imputer.predict_project(p.id)
                
                if prediction:
                    logger.info(f"Project {p.id}: Found gaps. Prediction: {prediction}")
                    metrics["imputed"] += 1
                    
                    if not dry_run:
                        imputer.save_imputation(p.id, prediction)
                else:
                    # No gaps found
                    pass
                    
                metrics["processed"] += 1
                
            except Exception as e:
                logger.error(f"Error processing Project {p.id}: {e}")
                
        logger.info(f"Completed. Scanned: {metrics['processed']}, Imputed: {metrics['imputed']}")

    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100, help="projects to scan")
    parser.add_argument("--dry-run", action="store_true", help="Do not save DB changes")
    args = parser.parse_args()
    
    run_imputation(limit=args.limit, dry_run=args.dry_run)
