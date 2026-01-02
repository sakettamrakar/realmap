"""
OCR Configuration Settings

Centralized configuration for OCR processing parameters.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class OCRConfig:
    """Configuration for OCR processing"""
    
    # Tesseract Configuration
    tesseract_cmd: str = field(default_factory=lambda: os.getenv(
        "TESSERACT_CMD", 
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    ))
    tesseract_lang: str = "eng+hin"  # English + Hindi
    tesseract_config: str = "--oem 3 --psm 3"  # LSTM engine, auto page segmentation (better for mixed layouts)
    
    # PDF Conversion Settings
    dpi: int = 400  # Higher DPI = better quality (increased from 300)
    image_format: str = "PNG"
    poppler_path: Optional[str] = field(default_factory=lambda: os.getenv(
        "POPPLER_PATH",
        r"C:\Program Files\poppler-24.02.0\Library\bin"
    ))
    
    # EasyOCR Configuration (fallback)
    use_easyocr_fallback: bool = False  # DISABLED - Tesseract is sufficient and 20-40x faster
    easyocr_langs: List[str] = field(default_factory=lambda: ["en", "hi"])
    easyocr_gpu: bool = True
    
    # Processing Settings
    max_pages: int = 50  # Maximum pages to process per PDF
    timeout_per_page: int = 30  # Seconds
    temp_dir: Optional[str] = None  # Use system temp if None
    
    # Text Cleaning Settings
    remove_special_chars: bool = True
    normalize_whitespace: bool = True
    fix_common_ocr_errors: bool = True
    
    # Quality Settings
    min_confidence: float = 0.0  # Accept all Tesseract results (confidence check disabled)
    enable_preprocessing: bool = True  # Image preprocessing before OCR
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        # Check Tesseract installation
        if not Path(self.tesseract_cmd).exists():
            # Try common alternative paths
            alternatives = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                "/usr/bin/tesseract",
                "/usr/local/bin/tesseract"
            ]
            for alt in alternatives:
                if Path(alt).exists():
                    self.tesseract_cmd = alt
                    break
        
        # Check Poppler installation
        if self.poppler_path and not Path(self.poppler_path).exists():
            alternatives = [
                r"C:\Program Files\poppler-24.02.0\Library\bin",
                r"C:\tools\poppler\bin",
                None  # Use system PATH
            ]
            for alt in alternatives:
                if alt is None or Path(alt).exists():
                    self.poppler_path = alt
                    break
    
    @classmethod
    def from_env(cls) -> "OCRConfig":
        """Create configuration from environment variables"""
        return cls(
            tesseract_cmd=os.getenv("TESSERACT_CMD", cls.tesseract_cmd),
            tesseract_lang=os.getenv("TESSERACT_LANG", "eng+hin"),
            dpi=int(os.getenv("OCR_DPI", "300")),
            use_easyocr_fallback=os.getenv("USE_EASYOCR", "true").lower() == "true",
            easyocr_gpu=os.getenv("EASYOCR_GPU", "true").lower() == "true",
            max_pages=int(os.getenv("OCR_MAX_PAGES", "50")),
            timeout_per_page=int(os.getenv("OCR_TIMEOUT", "30")),
        )
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {
            "tesseract_cmd": self.tesseract_cmd,
            "tesseract_lang": self.tesseract_lang,
            "tesseract_config": self.tesseract_config,
            "dpi": self.dpi,
            "image_format": self.image_format,
            "poppler_path": self.poppler_path,
            "use_easyocr_fallback": self.use_easyocr_fallback,
            "easyocr_langs": self.easyocr_langs,
            "easyocr_gpu": self.easyocr_gpu,
            "max_pages": self.max_pages,
            "timeout_per_page": self.timeout_per_page,
            "min_confidence": self.min_confidence,
            "enable_preprocessing": self.enable_preprocessing,
        }


# Global default configuration
DEFAULT_CONFIG = OCRConfig()
