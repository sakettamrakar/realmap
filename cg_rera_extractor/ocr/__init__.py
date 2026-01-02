"""
OCR Module for PDF Processing

This module provides OCR (Optical Character Recognition) capabilities
for extracting text from PDF documents.

Components:
- PDFConverter: Convert PDF pages to images
- OCREngine: Extract text from images using Tesseract/EasyOCR
- TextCleaner: Clean and normalize extracted text
- OCRConfig: Configuration settings for OCR processing

Usage:
    from cg_rera_extractor.ocr import PDFConverter, OCREngine, TextCleaner
    
    # Convert PDF to images
    converter = PDFConverter()
    images = converter.convert_pdf_to_images("document.pdf")
    
    # Extract text
    engine = OCREngine()
    text = engine.extract_text(images[0])
    
    # Clean text
    cleaner = TextCleaner()
    clean_text = cleaner.clean(text)
"""

from .pdf_converter import PDFConverter
from .ocr_engine import OCREngine
from .text_cleaner import TextCleaner
from .ocr_config import OCRConfig

__all__ = [
    "PDFConverter",
    "OCREngine", 
    "TextCleaner",
    "OCRConfig"
]
