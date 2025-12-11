#!/usr/bin/env python3
"""
CLI script to generate embeddings for all projects.

Usage:
    python scripts/generate_embeddings.py --limit 100
"""
import argparse
import logging
import sys
import os

sys.path.append(os.getcwd())

from sqlalchemy import select
from cg_rera_extractor.db.base import get_engine, get_session_local
from cg_rera_extractor.db.models import Project, ProjectEmbedding
from ai.chat.embedder import ProjectEmbedder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("generate_embeddings")


def generate_embeddings(limit: int = None, force: bool = False):
    """
    Generate embeddings for projects.
    
    Args:
        limit: Max projects to process.
        force: If True, regenerate even if embedding exists.
    """
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    session = SessionLocal()
    
    embedder = ProjectEmbedder()
    
    if not embedder.is_loaded:
        logger.error("Embedder model not loaded. Install sentence-transformers.")
        return
    
    try:
        # Query projects
        if force:
            stmt = select(Project)
        else:
            # Only projects without embeddings
            stmt = select(Project).outerjoin(ProjectEmbedding).where(ProjectEmbedding.id.is_(None))
        
        if limit:
            stmt = stmt.limit(limit)
        
        projects = session.scalars(stmt).all()
        logger.info(f"Found {len(projects)} projects to embed.")
        
        count = 0
        for project in projects:
            try:
                # Build text and generate embedding
                text_content = embedder.build_project_text(project)
                embedding = embedder.embed_text(text_content)
                
                if embedding:
                    # Check if embedding record exists
                    existing = session.query(ProjectEmbedding).filter_by(project_id=project.id).first()
                    
                    if existing:
                        existing.embedding_data = embedding
                        existing.text_content = text_content
                        existing.model_name = embedder.model_name
                    else:
                        emb_record = ProjectEmbedding(
                            project_id=project.id,
                            embedding_data=embedding,
                            text_content=text_content,
                            model_name=embedder.model_name
                        )
                        session.add(emb_record)
                    
                    # Also update native vector column if available
                    try:
                        from sqlalchemy import text as sql_text
                        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
                        session.execute(sql_text("""
                            UPDATE project_embeddings 
                            SET embedding = :vec::vector 
                            WHERE project_id = :pid
                        """), {"vec": embedding_str, "pid": project.id})
                    except Exception:
                        pass  # pgvector might not be available
                    
                    count += 1
                    
                    if count % 50 == 0:
                        session.commit()
                        logger.info(f"Progress: {count} embeddings generated...")
                        
            except Exception as e:
                logger.error(f"Error embedding project {project.id}: {e}")
                continue
        
        session.commit()
        logger.info(f"Completed. Generated {count} embeddings.")
        
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Max projects to process")
    parser.add_argument("--force", action="store_true", help="Regenerate existing embeddings")
    args = parser.parse_args()
    
    generate_embeddings(limit=args.limit, force=args.force)
