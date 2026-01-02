"""
OCR Engine - Text Extraction from Images

Provides OCR capabilities using Tesseract (primary) and EasyOCR (fallback).
Supports English and Hindi text extraction.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union
from dataclasses import dataclass
import os

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False

try:
    from PIL import Image
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from .ocr_config import OCRConfig, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result of OCR extraction"""
    text: str
    confidence: float
    engine: str  # 'tesseract' or 'easyocr'
    language: str
    success: bool
    error: Optional[str] = None
    word_count: int = 0
    
    def __post_init__(self):
        if self.text:
            self.word_count = len(self.text.split())


@dataclass
class PageOCRResult:
    """OCR result for a single page with detailed info"""
    page_number: int
    text: str
    confidence: float
    word_boxes: List[dict]  # Word-level bounding boxes
    success: bool
    error: Optional[str] = None


class OCREngine:
    """
    OCR Engine for extracting text from images.
    
    Features:
    - Primary: Tesseract OCR (fast, good accuracy)
    - Fallback: EasyOCR (better for mixed scripts)
    - Image preprocessing for better results
    - Confidence scoring
    - Multi-language support (English + Hindi)
    
    Usage:
        engine = OCREngine()
        result = engine.extract_text(image)
        print(result.text)
    """
    
    def __init__(self, config: Optional[OCRConfig] = None):
        """
        Initialize OCR engine.
        
        Args:
            config: OCR configuration. Uses default if not provided.
        """
        self.config = config or DEFAULT_CONFIG
        self._easyocr_reader = None
        self._setup_tesseract()
    
    def _setup_tesseract(self):
        """Configure Tesseract OCR"""
        if HAS_TESSERACT:
            # Set Tesseract path
            if os.path.exists(self.config.tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_cmd
            else:
                logger.warning(
                    f"Tesseract not found at {self.config.tesseract_cmd}. "
                    "Using system PATH."
                )
    
    def _get_easyocr_reader(self):
        """Lazy initialization of EasyOCR reader (GPU memory heavy)"""
        if self._easyocr_reader is None and HAS_EASYOCR:
            logger.info("Initializing EasyOCR reader...")
            try:
                self._easyocr_reader = easyocr.Reader(
                    self.config.easyocr_langs,
                    gpu=self.config.easyocr_gpu,
                    verbose=False
                )
                logger.info("EasyOCR reader initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                self._easyocr_reader = False  # Mark as failed
        return self._easyocr_reader if self._easyocr_reader else None
    
    def _preprocess_for_ocr(self, image: "Image.Image") -> "Image.Image":
        """
        Apply preprocessing to improve OCR accuracy.
        
        Args:
            image: PIL Image
            
        Returns:
            Preprocessed PIL Image
        """
        if not self.config.enable_preprocessing:
            return image
        
        try:
            # Convert to numpy array for OpenCV processing
            if HAS_CV2:
                img_array = np.array(image)
                
                # Convert to grayscale if needed
                if len(img_array.shape) == 3:
                    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                else:
                    gray = img_array
                
                # Apply adaptive thresholding for better text recognition
                # This helps with uneven lighting and faded documents
                binary = cv2.adaptiveThreshold(
                    gray, 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11, 2
                )
                
                # Denoise
                denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
                
                return Image.fromarray(denoised)
            else:
                # Fallback: Just ensure grayscale
                if image.mode != 'L':
                    image = image.convert('L')
                return image
                
        except Exception as e:
            logger.warning(f"Preprocessing failed: {e}")
            return image
    
    def extract_text(
        self,
        image: Union["Image.Image", str, np.ndarray],
        lang: Optional[str] = None
    ) -> OCRResult:
        """
        Extract text from an image using OCR.
        
        Args:
            image: PIL Image, file path, or numpy array
            lang: Language code(s) (e.g., 'eng', 'eng+hin')
            
        Returns:
            OCRResult with extracted text and metadata
        """
        lang = lang or self.config.tesseract_lang
        
        # Load image if path provided
        if isinstance(image, str):
            if not Path(image).exists():
                return OCRResult(
                    text="",
                    confidence=0.0,
                    engine="none",
                    language=lang,
                    success=False,
                    error=f"Image not found: {image}"
                )
            image = Image.open(image)
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # Preprocess image
        processed_image = self._preprocess_for_ocr(image)
        
        # Try Tesseract first (if available)
        if HAS_TESSERACT:
            try:
                result = self._extract_with_tesseract(processed_image, lang)
                if result.success and result.confidence >= self.config.min_confidence:
                    return result
                elif result.success:
                    logger.info(
                        f"Tesseract confidence ({result.confidence:.2f}) below threshold. "
                        f"Trying EasyOCR fallback."
                    )
            except Exception as e:
                logger.warning(f"Tesseract failed, falling back to EasyOCR: {e}")
        
        # Use EasyOCR (fallback or primary if Tesseract unavailable)
        if HAS_EASYOCR:
            result = self._extract_with_easyocr(processed_image)
            if result.success:
                return result
        
        # If both failed
        return OCRResult(
            text="",
            confidence=0.0,
            engine="none",
            language=lang,
            success=False,
            error="All OCR engines failed or unavailable. Install Tesseract or check EasyOCR setup."
        )
    
    def _extract_with_tesseract(
        self,
        image: "Image.Image",
        lang: str
    ) -> OCRResult:
        """
        Extract text using Tesseract OCR.
        
        Args:
            image: PIL Image
            lang: Tesseract language code
            
        Returns:
            OCRResult
        """
        try:
            # Get detailed data including confidence
            data = pytesseract.image_to_data(
                image,
                lang=lang,
                config=self.config.tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text and calculate average confidence
            texts = []
            confidences = []
            
            for i, text in enumerate(data['text']):
                conf = int(data['conf'][i])
                if conf > 0 and text.strip():  # Filter empty/low-confidence
                    texts.append(text)
                    confidences.append(conf)
            
            full_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Also get the full text extraction for better formatting
            full_text = pytesseract.image_to_string(
                image,
                lang=lang,
                config=self.config.tesseract_config
            )
            
            return OCRResult(
                text=full_text.strip(),
                confidence=avg_confidence / 100,  # Normalize to 0-1
                engine="tesseract",
                language=lang,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                engine="tesseract",
                language=lang,
                success=False,
                error=str(e)
            )
    
    def _extract_with_easyocr(self, image: "Image.Image") -> OCRResult:
        """
        Extract text using EasyOCR.
        
        Args:
            image: PIL Image
            
        Returns:
            OCRResult
        """
        reader = self._get_easyocr_reader()
        if reader is None:
            return OCRResult(
                text="",
                confidence=0.0,
                engine="easyocr",
                language=",".join(self.config.easyocr_langs),
                success=False,
                error="EasyOCR reader not available"
            )
        
        try:
            # Convert to numpy array
            img_array = np.array(image)
            
            # Run OCR
            results = reader.readtext(img_array)
            
            # Extract text and confidence
            texts = []
            confidences = []
            
            for (bbox, text, confidence) in results:
                texts.append(text)
                confidences.append(confidence)
            
            full_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return OCRResult(
                text=full_text.strip(),
                confidence=avg_confidence,
                engine="easyocr",
                language=",".join(self.config.easyocr_langs),
                success=True
            )
            
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                engine="easyocr",
                language=",".join(self.config.easyocr_langs),
                success=False,
                error=str(e)
            )
    
    def extract_text_from_pages(
        self,
        images: List["Image.Image"],
        lang: Optional[str] = None
    ) -> List[PageOCRResult]:
        """
        Extract text from multiple page images.
        
        Args:
            images: List of PIL Images
            lang: Language code
            
        Returns:
            List of PageOCRResult for each page
        """
        results = []
        
        for i, image in enumerate(images, start=1):
            logger.info(f"Processing page {i}/{len(images)}")
            
            result = self.extract_text(image, lang)
            
            page_result = PageOCRResult(
                page_number=i,
                text=result.text,
                confidence=result.confidence,
                word_boxes=[],  # Could be populated if needed
                success=result.success,
                error=result.error
            )
            results.append(page_result)
        
        return results
    
    def get_text_with_layout(
        self,
        image: "Image.Image",
        lang: Optional[str] = None
    ) -> Tuple[str, List[dict]]:
        """
        Extract text while preserving layout information.
        
        Args:
            image: PIL Image
            lang: Language code
            
        Returns:
            Tuple of (text, list of word boxes with coordinates)
        """
        lang = lang or self.config.tesseract_lang
        
        if not HAS_TESSERACT:
            return ("", [])
        
        try:
            data = pytesseract.image_to_data(
                image,
                lang=lang,
                config=self.config.tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            words = []
            text_lines = {}
            
            for i, text in enumerate(data['text']):
                if text.strip():
                    word_info = {
                        'text': text,
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'confidence': data['conf'][i],
                        'line_num': data['line_num'][i],
                        'block_num': data['block_num'][i]
                    }
                    words.append(word_info)
                    
                    # Group by line for text reconstruction
                    line_key = (data['block_num'][i], data['line_num'][i])
                    if line_key not in text_lines:
                        text_lines[line_key] = []
                    text_lines[line_key].append((data['left'][i], text))
            
            # Reconstruct text preserving line structure
            lines = []
            for key in sorted(text_lines.keys()):
                line_words = sorted(text_lines[key], key=lambda x: x[0])
                lines.append(' '.join(w[1] for w in line_words))
            
            return ('\n'.join(lines), words)
            
        except Exception as e:
            logger.error(f"Layout extraction failed: {e}")
            return ("", [])
    
    def check_availability(self) -> dict:
        """
        Check which OCR engines are available.
        
        Returns:
            Dictionary with availability status
        """
        status = {
            "tesseract": {
                "installed": HAS_TESSERACT,
                "executable_found": False,
                "version": None
            },
            "easyocr": {
                "installed": HAS_EASYOCR,
                "gpu_available": False
            },
            "opencv": {
                "installed": HAS_CV2
            },
            "pillow": {
                "installed": HAS_PIL
            }
        }
        
        # Check Tesseract executable
        if HAS_TESSERACT:
            try:
                version = pytesseract.get_tesseract_version()
                status["tesseract"]["executable_found"] = True
                status["tesseract"]["version"] = str(version)
            except Exception:
                pass
        
        # Check EasyOCR GPU
        if HAS_EASYOCR:
            try:
                import torch
                status["easyocr"]["gpu_available"] = torch.cuda.is_available()
            except ImportError:
                pass
        
        return status


# Convenience function
def extract_text(image: Union["Image.Image", str]) -> str:
    """
    Quick function to extract text from an image.
    
    Args:
        image: PIL Image or path to image file
        
    Returns:
        Extracted text string
    """
    engine = OCREngine()
    result = engine.extract_text(image)
    return result.text
