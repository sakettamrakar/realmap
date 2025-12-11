#!/usr/bin/env python3
"""
CLI script to process floor plan artifacts using AI OCR.
Enrich ProjectArtifacts with structured room data.

Usage:
    python scripts/process_floor_plans.py --limit 10
"""
import argparse
import logging
import os
import tempfile
import requests
from typing import Optional

from sqlalchemy import select, and_
from cg_rera_extractor.db.base import get_engine, get_session_local
from cg_rera_extractor.db.models import ProjectArtifact
from ai.ocr.parser import FloorPlanParser

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("process_floor_plans")

def download_file(url: str, dest_path: str) -> bool:
    """Download file from URL to destination."""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def process_artifacts(limit: int = 10, project_id: Optional[int] = None, dry_run: bool = False):
    """Main processing loop."""
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    session = SessionLocal()
    
    parser = FloorPlanParser()
    if not parser.models_loaded:
        logger.error("OCR models could not be loaded. Aborting.")
        return

    try:
        # Build query
        query = select(ProjectArtifact).where(
            ProjectArtifact.artifact_type.ilike("%floor%plan%"),
            ProjectArtifact.floor_plan_data.is_(None)
        )
        
        if project_id:
            query = query.where(ProjectArtifact.project_id == project_id)
            
        query = query.limit(limit)
        
        artifacts = session.scalars(query).all()
        logger.info(f"Found {len(artifacts)} artifacts to process.")
        
        processed_count = 0
        
        for artifact in artifacts:
            logger.info(f"Processing Artifact ID {artifact.id}...")
            
            # Determine file path
            local_path = artifact.file_path
            temp_file = None
            
            # If path doesn't exist locally, try URL
            if not local_path or not os.path.exists(local_path):
                if artifact.source_url:
                    logger.info(f"File not found locally, downloading from {artifact.source_url}...")
                    fd, temp_path = tempfile.mkstemp(suffix=f".{artifact.file_format or 'jpg'}")
                    os.close(fd)
                    temp_file = temp_path
                    if download_file(artifact.source_url, temp_file):
                        local_path = temp_file
                    else:
                        logger.warning(f"Could not retrieve file for Artifact {artifact.id}. Skipping.")
                        continue
                else:
                    logger.warning(f"No valid file path or URL for Artifact {artifact.id}. Skipping.")
                    continue
            
            # Parse
            try:
                result = parser.parse_image(local_path)
                
                if result.get("parsed"):
                   logger.info(f"Successfully parsed Artifact {artifact.id}. Found {len(result.get('rooms', []))} rooms.")
                   if not dry_run:
                       artifact.floor_plan_data = result
                       session.add(artifact)
                       session.commit()
                       processed_count += 1
                else:
                    logger.warning(f"Failed to parse Artifact {artifact.id}: {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Exception during parsing Artifact {artifact.id}: {e}")
            finally:
                # Cleanup temp file
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
                    
        logger.info(f"Completed. Processed {processed_count} artifacts.")
        
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10, help="Max artifacts to process")
    parser.add_argument("--project-id", type=int, help="Filter by specific project ID")
    parser.add_argument("--dry-run", action="store_true", help="Do not save changes to DB")
    args = parser.parse_args()
    
    process_artifacts(limit=args.limit, project_id=args.project_id, dry_run=args.dry_run)
