#!/usr/bin/env python3
"""
Debug LLM extraction on a specific PDF.
"""
import os
import sys
import time
import traceback

# Set environment before imports
os.environ["MODEL_PATH"] = "C:/models/ai/general/v1/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"
os.environ["GPU_LAYERS"] = "35"
os.environ["CONTEXT_SIZE"] = "8192"
os.environ["LLM_TIMEOUT_SEC"] = "180"

from pathlib import Path

print("=" * 70)
print("DEBUG LLM EXTRACTION")
print("=" * 70)

# PDF with minimal text
pdf_path = Path(r"C:\GIT\realmap\outputs\raipur-20\runs\run_20251210_090333_f88ae6\previews\PCGRERA250518000012\doc_01_Registration_Certificate.pdf")

print(f"\nPDF: {pdf_path.name}")

# Extract text first
from pypdf import PdfReader
reader = PdfReader(str(pdf_path))
text = ""
for page in reader.pages:
    text += page.extract_text() or ""
    
print(f"Extracted text length: {len(text)}")
print(f"Text preview: {repr(text[:200])}")

# Import and test classification
print("\n--- Testing Classification ---")
from ai.features.pdf_processing.llm_extractor import LLMExtractor, DOCUMENT_CLASSIFICATION_PROMPT, DocumentType

extractor = LLMExtractor()

# Test classification directly
try:
    truncated = text[:2000] if len(text) > 50 else "This is a registration certificate document"
    prompt = DOCUMENT_CLASSIFICATION_PROMPT.format(text=truncated)
    print(f"Prompt length: {len(prompt)}")
    
    from ai.llm.adapter import run as llm_run
    result = llm_run(prompt, max_tokens=50, temperature=0.1)
    print(f"LLM Response: {repr(result['text'])}")
    print(f"Error: {result.get('error')}")
    
    # Try parsing
    response_upper = result['text'].upper().strip()
    print(f"Parsed response: {repr(response_upper)}")
    
    # Check what category it matches
    type_mapping = {
        "BUILDING_PERMISSION": DocumentType.BUILDING_PERMISSION,
        "NOC": DocumentType.NOC,
        "LAYOUT_PLAN": DocumentType.LAYOUT_PLAN,
        "REGISTRATION": DocumentType.REGISTRATION,
        "AGREEMENT": DocumentType.AGREEMENT,
        "LAND_RECORD": DocumentType.LAND_RECORD,
        "COMPLETION": DocumentType.COMPLETION,
        "ENVIRONMENTAL": DocumentType.ENVIRONMENTAL,
        "FIRE_SAFETY": DocumentType.FIRE_SAFETY,
        "FINANCIAL": DocumentType.FINANCIAL,
        "OTHER": DocumentType.OTHER,
    }
    
    matched = None
    for key, doc_type in type_mapping.items():
        if key in response_upper:
            matched = (key, doc_type)
            print(f"Matched: {key} -> {doc_type}")
            break
    
    if not matched:
        print("No match found - will return UNKNOWN")

except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

# Now test full processing
print("\n--- Testing Full Processing ---")
try:
    result = extractor.process(pdf_path)
    print(f"Success: {result.success}")
    print(f"Document Type: {result.document_type}")
    print(f"Error: {result.error}")
    print(f"Warnings: {result.warnings}")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
