"""
PDF to Image Converter

Converts PDF documents to images for OCR processing.
Uses pdf2image library with Poppler backend.
"""

import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

try:
    from pdf2image import convert_from_path, pdfinfo_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from .ocr_config import OCRConfig, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """Result of PDF to image conversion"""
    images: List["Image.Image"]
    page_count: int
    source_path: str
    dpi: int
    success: bool
    error: Optional[str] = None
    
    @property
    def image_count(self) -> int:
        return len(self.images)


class PDFConverter:
    """
    Convert PDF documents to images for OCR processing.
    
    This class handles:
    - PDF to image conversion using pdf2image
    - Multi-page PDF support
    - Image preprocessing for better OCR results
    - Memory-efficient processing for large PDFs
    
    Usage:
        converter = PDFConverter()
        result = converter.convert_pdf_to_images("document.pdf")
        for image in result.images:
            # Process each page image
            pass
    """
    
    def __init__(self, config: Optional[OCRConfig] = None):
        """
        Initialize PDF converter.
        
        Args:
            config: OCR configuration. Uses default if not provided.
        """
        self.config = config or DEFAULT_CONFIG
        self._validate_dependencies()
    
    def _validate_dependencies(self):
        """Check that required dependencies are available"""
        if not HAS_PDF2IMAGE:
            raise ImportError(
                "pdf2image is required for PDF conversion. "
                "Install with: pip install pdf2image"
            )
        if not HAS_PIL:
            raise ImportError(
                "Pillow is required for image processing. "
                "Install with: pip install Pillow"
            )
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """
        Get PDF metadata without converting.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with PDF metadata (pages, size, etc.)
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        try:
            info = pdfinfo_from_path(
                str(pdf_path),
                poppler_path=self.config.poppler_path
            )
            return {
                "pages": info.get("Pages", 0),
                "title": info.get("Title", ""),
                "author": info.get("Author", ""),
                "creator": info.get("Creator", ""),
                "producer": info.get("Producer", ""),
                "creation_date": info.get("CreationDate", ""),
                "file_size": pdf_path.stat().st_size,
            }
        except Exception as e:
            logger.warning(f"Could not get PDF info: {e}")
            return {"pages": 0, "error": str(e)}
    
    def convert_pdf_to_images(
        self,
        pdf_path: str,
        first_page: int = 1,
        last_page: Optional[int] = None,
        dpi: Optional[int] = None
    ) -> ConversionResult:
        """
        Convert PDF pages to images.
        
        Args:
            pdf_path: Path to PDF file
            first_page: First page to convert (1-indexed)
            last_page: Last page to convert (None = all pages)
            dpi: DPI for conversion (None = use config default)
            
        Returns:
            ConversionResult with list of PIL Image objects
        """
        pdf_path = Path(pdf_path)
        dpi = dpi or self.config.dpi
        
        if not pdf_path.exists():
            return ConversionResult(
                images=[],
                page_count=0,
                source_path=str(pdf_path),
                dpi=dpi,
                success=False,
                error=f"PDF not found: {pdf_path}"
            )
        
        # Get page count
        info = self.get_pdf_info(str(pdf_path))
        total_pages = info.get("pages", 0)
        
        if total_pages == 0:
            return ConversionResult(
                images=[],
                page_count=0,
                source_path=str(pdf_path),
                dpi=dpi,
                success=False,
                error="Could not determine page count or PDF is empty"
            )
        
        # Apply page limits
        if last_page is None:
            last_page = min(total_pages, self.config.max_pages)
        else:
            last_page = min(last_page, total_pages, self.config.max_pages)
        
        logger.info(f"Converting PDF: {pdf_path.name} (pages {first_page}-{last_page} of {total_pages})")
        
        try:
            # Convert PDF to images
            images = convert_from_path(
                str(pdf_path),
                dpi=dpi,
                first_page=first_page,
                last_page=last_page,
                fmt=self.config.image_format.lower(),
                poppler_path=self.config.poppler_path,
                thread_count=2,  # Parallel conversion
                use_cropbox=True,
                strict=False
            )
            
            # Apply preprocessing if enabled
            if self.config.enable_preprocessing:
                images = [self._preprocess_image(img) for img in images]
            
            logger.info(f"Converted {len(images)} pages from {pdf_path.name}")
            
            return ConversionResult(
                images=images,
                page_count=total_pages,
                source_path=str(pdf_path),
                dpi=dpi,
                success=True
            )
            
        except Exception as e:
            logger.error(f"PDF conversion failed: {e}")
            return ConversionResult(
                images=[],
                page_count=total_pages,
                source_path=str(pdf_path),
                dpi=dpi,
                success=False,
                error=str(e)
            )
    
    def _preprocess_image(self, image: "Image.Image") -> "Image.Image":
        """
        Preprocess image for better OCR results.
        
        Applies:
        - Grayscale conversion
        - Contrast enhancement
        - Denoising (optional)
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast using simple threshold-based approach
            # This helps with faded documents
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Sharpen slightly
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)
            
            return image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image
    
    def convert_image_file(self, image_path: str) -> Optional["Image.Image"]:
        """
        Load and preprocess an image file (JPG, PNG, etc.)
        
        Args:
            image_path: Path to image file
            
        Returns:
            PIL Image object or None if failed
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            return None
        
        try:
            image = Image.open(str(image_path))
            
            if self.config.enable_preprocessing:
                image = self._preprocess_image(image)
            
            return image
            
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            return None
    
    def save_images(
        self,
        images: List["Image.Image"],
        output_dir: str,
        prefix: str = "page"
    ) -> List[str]:
        """
        Save converted images to disk.
        
        Args:
            images: List of PIL Image objects
            output_dir: Directory to save images
            prefix: Filename prefix
            
        Returns:
            List of saved file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        for i, image in enumerate(images, start=1):
            filename = f"{prefix}_{i:03d}.{self.config.image_format.lower()}"
            filepath = output_dir / filename
            
            try:
                image.save(str(filepath))
                saved_paths.append(str(filepath))
            except Exception as e:
                logger.error(f"Failed to save image {filename}: {e}")
        
        return saved_paths


# Convenience function
def convert_pdf(pdf_path: str, **kwargs) -> ConversionResult:
    """
    Quick function to convert a PDF to images.
    
    Args:
        pdf_path: Path to PDF file
        **kwargs: Additional arguments for convert_pdf_to_images
        
    Returns:
        ConversionResult with images
    """
    converter = PDFConverter()
    return converter.convert_pdf_to_images(pdf_path, **kwargs)
