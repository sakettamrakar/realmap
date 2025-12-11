"""
RERA PDF Parser module.
Implements extraction logic using OCR and LLM as defined in the prompt.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

# Try importing PDF libraries
try:
    from pdf2image import convert_from_path
    import pytesseract
except ImportError:
    convert_from_path = None
    pytesseract = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

from ai.schemas import ReraExtractionResult

logger = logging.getLogger(__name__)

class ReraPdfParser:
    def __init__(self, use_ocr: bool = True):
        self.use_ocr = use_ocr
        if use_ocr and (convert_from_path is None or pytesseract is None):
            logger.warning("OCR libraries not found. Falling back to simple text extraction.")
            self.use_ocr = False
            
    def extract_text(self, file_path: str, max_pages: int = 5) -> str:
        """Extracts text from PDF using OCR or simple extraction."""
        text = ""
        
        # Validate PDF file first
        if not self._validate_pdf(file_path):
            raise ValueError(f"Invalid or corrupt PDF file: {file_path}")
        
        if self.use_ocr:
            try:
                images = convert_from_path(file_path, first_page=1, last_page=max_pages)
                for i, image in enumerate(images):
                    page_text = pytesseract.image_to_string(image)
                    text += f"--- Page {i+1} ---\n{page_text}\n"
                return text
            except Exception as e:
                logger.error(f"OCR Failed: {e}. Falling back to pypdf.")
        
        # Fallback or default to pypdf
        if PdfReader:
            try:
                reader = PdfReader(file_path)
                num_pages = min(len(reader.pages), max_pages)
                for i in range(num_pages):
                    page = reader.pages[i]
                    text += f"--- Page {i+1} ---\n{page.extract_text()}\n"
            except Exception as e:
                logger.error(f"PDF Reading Failed: {e}")
                raise ValueError(f"Failed to read PDF: {e}")
        else:
            logger.error("No PDF library available.")
            raise RuntimeError("No PDF parsing library available")
            
        return text
    
    def _validate_pdf(self, file_path: str) -> bool:
        """Validates that the file is a proper PDF."""
        try:
            # Check file size (must be > 0)
            if os.path.getsize(file_path) == 0:
                logger.error("PDF file is empty")
                return False
            
            # Check PDF header
            with open(file_path, 'rb') as f:
                header = f.read(5)
                if not header.startswith(b'%PDF-'):
                    logger.error(f"Invalid PDF header: {header}")
                    return False
            
            # Try to open with PdfReader if available
            if PdfReader:
                try:
                    reader = PdfReader(file_path)
                    # Check if we can read at least the metadata
                    _ = reader.metadata
                    # Check if there's at least one page
                    if len(reader.pages) == 0:
                        logger.error("PDF has no pages")
                        return False
                except Exception as e:
                    logger.error(f"PDF validation failed: {e}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error during PDF validation: {e}")
            return False

    def parse_with_llm(self, raw_text: str) -> Dict[str, Any]:
        """
        Sends raw text to LLM to extract structured fields.
        """
        # TODO: Implement connection to Qwen/Local LLM Adapter
        # For now, mocking the response or using a dummy extractor
        
        # In a real scenario, this would import the `call_llm` function 
        # from ai.llm.adapter and pass the prompt from `docs/prompts/ai_prompts/02_rera_doc_parser_prompt.md`
        
        prompt = f"""
        Extract the following fields from the RERA document text below:
        - Proposed Completion Date (YYYY-MM-DD)
        - Litigation Count (Integer)
        - Architect Name (String)
        
        Text:
        {raw_text[:4000]} # Truncate to avoid context limit in prototype
        
        Return JSON only.
        """
        
        # Mock Response for prototype
        return {
            "proposed_completion_date": None,
            "litigation_count": 0,
            "architect_name": None,
            "mock": True
        }

    def process_file(self, file_path: str, project_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """
        Main entry point. extracts text, parses, and saves to DB.
        Returns None if processing fails (invalid PDF, errors, etc.)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # 1. Extract (will raise ValueError for invalid PDFs)
            raw_text = self.extract_text(file_path)
            
            # 2. Parse
            extracted_data = self.parse_with_llm(raw_text)
            
            # 3. Save to DB (using the ReraFiling model we just added)
            # Note: Importing here to avoid circular dependencies if called from main
            from cg_rera_extractor.db.models import ReraFiling
            
            filing = ReraFiling(
                project_id=project_id,
                file_path=file_path,
                file_name=os.path.basename(file_path),
                doc_type="Unknown", # Logic to infer type could go here
                raw_text=raw_text,
                extracted_data=extracted_data,
                model_name="rules-v1",
                confidence_score=0.5
            )
            
            db.add(filing)
            db.commit()
            db.refresh(filing)
            
            return {
                "filing_id": filing.id,
                "data": extracted_data
            }
        except (ValueError, RuntimeError) as e:
            # Invalid or corrupt PDF - log and return None
            logger.warning(f"PDF processing failed for {file_path}: {e}")
            return None
        except Exception as e:
            # Unexpected error - log and re-raise
            logger.error(f"Unexpected error processing {file_path}: {e}")
            raise
