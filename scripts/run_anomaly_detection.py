#!/usr/bin/env python3
"""
CLI script to run AI-based anomaly detection on project data.
Flags outliers in Price/Area ratios.

Usage:
    python scripts/run_anomaly_detection.py --dry-run
"""
import argparse
import logging
import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from cg_rera_extractor.db.base import get_engine, get_session_local
from ai.anomaly.detector import AnomalyDetector

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("run_anomaly_detection")

def run_detection(dry_run: bool = False):
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    session = SessionLocal()
    
    try:
        detector = AnomalyDetector(session)
        
        # 1. Load Data
        df = detector.load_data()
        if df.empty:
            logger.warning("No data found for anomaly detection.")
            return

        # 2. Train Model
        logger.info("Training Anomaly Detector...")
        detector.train(df)
        
        # 3. Detect
        logger.info("Running detection...")
        anomalies = detector.detect(df)
        
        if anomalies:
            logger.info(f"Found {len(anomalies)} anomalies.")
            if not dry_run:
                detector.save_flags(anomalies)
        else:
            logger.info("No anomalies detected.")
            
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Do not save DB changes")
    args = parser.parse_args()
    
    run_detection(dry_run=args.dry_run)
