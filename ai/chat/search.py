"""
Semantic Search using pgvector.
"""
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from cg_rera_extractor.db.models import Project, ProjectEmbedding
from .embedder import ProjectEmbedder

logger = logging.getLogger("ai.chat.search")


class SemanticSearch:
    """
    Performs semantic similarity search on projects using pgvector.
    """
    
    def __init__(self, session: Session, embedder: ProjectEmbedder = None):
        self.session = session
        self.embedder = embedder or ProjectEmbedder()
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for projects similar to the query.
        
        Args:
            query: Natural language search query.
            limit: Maximum number of results.
            
        Returns:
            List of dicts with project_id, name, score.
        """
        if not self.embedder.is_loaded:
            logger.error("Embedder not loaded. Cannot search.")
            return []
        
        # 1. Generate query embedding
        query_embedding = self.embedder.embed_text(query)
        if not query_embedding:
            logger.warning("Failed to generate query embedding.")
            return []
        
        # 2. Run pgvector similarity search
        # Using cosine similarity (1 - cosine_distance)
        # The <=> operator is cosine distance in pgvector
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        sql = text("""
            SELECT 
                pe.project_id,
                p.project_name,
                1 - (pe.embedding <=> :query_vec::vector) as similarity
            FROM project_embeddings pe
            JOIN projects p ON p.id = pe.project_id
            WHERE pe.embedding IS NOT NULL
            ORDER BY pe.embedding <=> :query_vec::vector
            LIMIT :limit
        """)
        
        try:
            result = self.session.execute(sql, {
                "query_vec": embedding_str,
                "limit": limit
            })
            
            matches = []
            for row in result:
                matches.append({
                    "project_id": row.project_id,
                    "name": row.project_name,
                    "score": round(float(row.similarity), 4)
                })
            
            logger.info(f"Found {len(matches)} matches for query: '{query[:50]}...'")
            return matches
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_fallback(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fallback search using JSON embeddings if pgvector is not available.
        Uses Python-side cosine similarity (slower).
        """
        import numpy as np
        
        query_embedding = self.embedder.embed_text(query)
        if not query_embedding:
            return []
        
        query_vec = np.array(query_embedding)
        
        # Load all embeddings
        stmt = select(ProjectEmbedding).where(ProjectEmbedding.embedding_data.is_not(None))
        embeddings = self.session.scalars(stmt).all()
        
        scores = []
        for emb in embeddings:
            if emb.embedding_data:
                doc_vec = np.array(emb.embedding_data)
                # Cosine similarity
                sim = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
                scores.append((emb.project_id, float(sim)))
        
        # Sort by similarity
        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for pid, score in scores[:limit]:
            project = self.session.get(Project, pid)
            results.append({
                "project_id": pid,
                "name": project.project_name if project else "Unknown",
                "score": round(score, 4)
            })
        
        return results
