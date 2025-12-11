"""
Project Embedder for semantic search.
Uses SentenceTransformers to generate embeddings.
"""
import logging
from typing import List, Optional

logger = logging.getLogger("ai.chat.embedder")

# Lazy load to avoid import errors if not installed
SENTENCE_TRANSFORMERS_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers not installed. Embeddings will not work.")


class ProjectEmbedder:
    """
    Generates vector embeddings for projects using SentenceTransformers.
    Default model: all-MiniLM-L6-v2 (384 dimensions, ~90MB)
    """
    
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DIM = 384
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or self.MODEL_NAME
        self.model = None
        self.is_loaded = False
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self._load_model()
    
    def _load_model(self):
        """Load the SentenceTransformer model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.is_loaded = True
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.is_loaded = False
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a text string.
        
        Args:
            text: Input text to embed.
            
        Returns:
            List of floats (384 dimensions) or None if model not loaded.
        """
        if not self.is_loaded:
            logger.warning("Model not loaded. Cannot generate embedding.")
            return None
            
        if not text or not text.strip():
            return None
            
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def embed_project(self, project) -> Optional[List[float]]:
        """
        Generate embedding for a Project object.
        Builds a text representation from project attributes.
        
        Args:
            project: Project ORM object.
            
        Returns:
            Embedding vector or None.
        """
        text = self.build_project_text(project)
        return self.embed_text(text)
    
    def build_project_text(self, project) -> str:
        """
        Build searchable text from project attributes.
        Combines: name, location, amenities, unit types, developer.
        """
        parts = []
        
        # Project name
        if project.project_name:
            parts.append(project.project_name)
        
        # Location
        location_parts = []
        if hasattr(project, 'village_or_locality') and project.village_or_locality:
            location_parts.append(project.village_or_locality)
        if hasattr(project, 'district') and project.district:
            location_parts.append(project.district)
        if hasattr(project, 'state_code') and project.state_code:
            location_parts.append(project.state_code)
        if location_parts:
            parts.append(f"Location: {', '.join(location_parts)}")
        
        # Unit types (e.g., "1BHK, 2BHK, 3BHK")
        if hasattr(project, 'unit_types') and project.unit_types:
            unit_labels = set()
            for ut in project.unit_types:
                if ut.name:
                    unit_labels.add(ut.name)
            if unit_labels:
                parts.append(f"Units: {', '.join(sorted(unit_labels))}")
        
        # Amenities
        if hasattr(project, 'amenities_list') and project.amenities_list:
            parts.append(f"Amenities: {', '.join(project.amenities_list[:10])}")
        
        # Developer/Promoter
        if hasattr(project, 'promoters') and project.promoters:
            promoter_names = [p.name for p in project.promoters if p.name]
            if promoter_names:
                parts.append(f"Developer: {', '.join(promoter_names[:2])}")
        
        # Price range (if available)
        if hasattr(project, 'pricing_snapshots') and project.pricing_snapshots:
            latest = project.pricing_snapshots[-1]
            if latest.min_price_total and latest.max_price_total:
                parts.append(f"Price: {latest.min_price_total} - {latest.max_price_total}")
        
        return ". ".join(parts)
