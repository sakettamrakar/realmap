import os
import logging
import json
from typing import Dict, Any, List, Optional
from PIL import Image
import numpy as np

# Configure logging
logger = logging.getLogger("ai.ocr.parser")

# Global flag for dependency availability
SURYA_AVAILABLE = False
try:
    from surya.ocr import run_ocr
    from surya.model.detection import segformer
    from surya.model.recognition.model import load_model
    from surya.model.recognition.processor import load_processor
    SURYA_AVAILABLE = True
except ImportError:
    logger.warning("surya-ocr not installed. strict OCR features will be disabled.")

class FloorPlanParser:
    """
    Parser for floor plan images to extract room dimensions and layout.
    Uses Surya OCR for text detection and recognition.
    """
    
    def __init__(self, languages: List[str] = None):
        self.languages = languages or ["en"]
        self.ocr_model = None
        self.ocr_processor = None
        self.det_model = None
        self.det_processor = None
        
        if SURYA_AVAILABLE:
            try:
                self._load_models()
            except Exception as e:
                logger.error(f"Failed to load Surya models: {e}")
                self.models_loaded = False
        else:
            self.models_loaded = False

    def _load_models(self):
        """Lazy load models."""
        logger.info("Loading Surya OCR models...")
        self.det_processor, self.det_model = segformer.load_processor(), segformer.load_model()
        self.ocr_model = load_model()
        self.ocr_processor = load_processor()
        self.models_loaded = True
        logger.info("Surya models loaded successfully.")

    def parse_image(self, image_path: str) -> Dict[str, Any]:
        """
        Main entry point to parse a floor plan image.
        
        Args:
            image_path: Absolute path to the image file.
            
        Returns:
            Dict containing detected text, rooms, and raw OCR data.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        result = {
            "image_path": image_path,
            "parsed": False,
            "rooms": [],
            "raw_text": [],
            "meta": {}
        }
        
        if not self.models_loaded:
            result["error"] = "OCR dependencies not available"
            return result

        try:
            image = Image.open(image_path)
            
            # 1. Run OCR
            predictions = run_ocr(
                [image], 
                [self.languages], 
                self.det_model, 
                self.det_processor, 
                self.ocr_model, 
                self.ocr_processor
            )
            
            # 2. Process predictions
            # Surya returns a list of results (one per image)
            if predictions and len(predictions) > 0:
                ocr_result = predictions[0]
                
                # Extract text lines
                text_lines = []
                for line in ocr_result.text_lines:
                    text_lines.append({
                        "text": line.text,
                        "bbox": line.bbox, # [x1, y1, x2, y2]
                        "confidence": line.confidence
                    })
                
                result["raw_text"] = text_lines
                result["parsed"] = True
                
                # 3. Simple Heuristic Room Extraction (Placeholder)
                # In a real impl, we'd use geometric analysis here.
                # For now, we just identify text that looks like dimensions (e.g., "10'x12'")
                result["rooms"] = self._extract_rooms_from_text(text_lines)
                
        except Exception as e:
            logger.error(f"Error parsing image {image_path}: {e}")
            result["error"] = str(e)
            
        return result

    def _extract_rooms_from_text(self, text_lines: List[Dict]) -> List[Dict]:
        """
        Heuristic to pair room names with dimensions.
        Looks for patterns like '10x12', '1200 sqft', etc.
        """
        rooms = []
        # Basic heuristic: just store lines that look like dimensions
        # Real logic would proximity match "Bedroom" with "10'x12'"
        for item in text_lines:
            text = item["text"].lower()
            if "x" in text and any(c.isdigit() for c in text):
                rooms.append({
                    "label": "potential_dim",
                    "text": item["text"],
                    "bbox": item["bbox"]
                })
            elif "bedroom" in text or "kitchen" in text or "living" in text:
                rooms.append({
                    "label": "potential_room_name",
                    "text": item["text"],
                    "bbox": item["bbox"]
                })
        
        return rooms
