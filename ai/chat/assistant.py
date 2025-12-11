"""
Chat Assistant for natural language property search.
"""
import logging
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from cg_rera_extractor.db.models import Project
from .search import SemanticSearch
from .embedder import ProjectEmbedder

logger = logging.getLogger("ai.chat.assistant")

# Try to import LLM adapter for response synthesis
LLM_AVAILABLE = False
try:
    from ai.llm.adapter import get_llm_instance
    LLM_AVAILABLE = True
except ImportError:
    logger.warning("LLM adapter not available. Will return raw results only.")


class ChatAssistant:
    """
    Natural language chat interface for property search.
    Combines semantic search with LLM response synthesis.
    """
    
    def __init__(self, session: Session, embedder: ProjectEmbedder = None):
        self.session = session
        self.embedder = embedder or ProjectEmbedder()
        self.searcher = SemanticSearch(session, self.embedder)
        self.llm = None
        
        if LLM_AVAILABLE:
            try:
                self.llm = get_llm_instance()
            except Exception as e:
                logger.warning(f"Could not load LLM: {e}")
    
    def answer(self, user_query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Process a user query and return matching projects with a natural language answer.
        
        Args:
            user_query: The natural language question from the user.
            limit: Maximum number of projects to return.
            
        Returns:
            Dict with 'answer' (string) and 'projects' (list).
        """
        result = {
            "query": user_query,
            "answer": "",
            "projects": [],
            "success": False
        }
        
        # 1. Search for matching projects
        try:
            matches = self.searcher.search(user_query, limit=limit)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            # Try fallback
            try:
                matches = self.searcher.search_fallback(user_query, limit=limit)
            except Exception as e2:
                logger.error(f"Fallback search also failed: {e2}")
                result["answer"] = "I'm sorry, I couldn't search the database right now."
                return result
        
        if not matches:
            result["answer"] = "I couldn't find any projects matching your criteria."
            result["success"] = True
            return result
        
        # 2. Enrich results with project details
        enriched = []
        for match in matches:
            project = self.session.get(Project, match["project_id"])
            if project:
                enriched.append({
                    "id": project.id,
                    "name": project.project_name,
                    "location": getattr(project, 'village_or_locality', None) or getattr(project, 'district', None),
                    "score": match["score"]
                })
        
        result["projects"] = enriched
        
        # 3. Generate natural language response
        if self.llm and enriched:
            result["answer"] = self._synthesize_answer(user_query, enriched)
        else:
            # Simple fallback answer
            project_names = [p["name"] for p in enriched[:3] if p["name"]]
            if project_names:
                result["answer"] = f"I found {len(enriched)} projects that might match your search. Top matches: {', '.join(project_names)}."
            else:
                result["answer"] = f"I found {len(enriched)} potentially matching projects."
        
        result["success"] = True
        return result
    
    def _synthesize_answer(self, query: str, projects: List[Dict]) -> str:
        """
        Use LLM to generate a natural language summary of search results.
        """
        if not self.llm:
            return ""
        
        # Build context
        project_list = "\n".join([
            f"- {p['name']} in {p.get('location', 'Unknown location')}" 
            for p in projects[:5]
        ])
        
        prompt = f"""You are a helpful real estate assistant. The user asked: "{query}"

Based on a semantic search, here are the top matching projects:
{project_list}

Provide a brief, friendly response summarizing these results. Be concise (2-3 sentences max)."""

        try:
            response = self.llm(prompt, max_tokens=150)
            return response.strip() if response else ""
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            return ""
