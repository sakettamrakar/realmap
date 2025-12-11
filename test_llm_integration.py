#!/usr/bin/env python3
"""
Test integration with LLM mode explicitly.
"""
import os
import sys
import logging

# Force environment
os.environ["MODEL_PATH"] = "C:/models/ai/general/v1/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"
os.environ["GPU_LAYERS"] = "35"
os.environ["CONTEXT_SIZE"] = "8192"

logging.basicConfig(level=logging.INFO)

from pathlib import Path

# Test LLM extractor directly
print("=" * 60)
print("TESTING LLM EXTRACTOR INTEGRATION")
print("=" * 60)

print("\n1. Checking GPU...")
import subprocess
result = subprocess.run(
    ["nvidia-smi", "--query-gpu=name,memory.free", "--format=csv,noheader"],
    capture_output=True, text=True
)
print(f"   GPU: {result.stdout.strip()}")

print("\n2. Initializing LLM Extractor...")
from ai.features.pdf_processing import LLMExtractor

extractor = LLMExtractor(max_pages=10, max_tokens=256)
print(f"   Name: {extractor.name}")
print(f"   Version: {extractor.version}")

print("\n3. Testing extraction on a PDF with text...")
pdf_path = Path(r"C:\GIT\realmap\outputs\raipur-20\runs\run_20251210_090333_f88ae6\previews\PCGRERA250518000012\doc_32_CA_Certificate.pdf")

if pdf_path.exists():
    import time
    start = time.time()
    result = extractor.process(pdf_path)
    elapsed = time.time() - start
    
    print(f"   Success: {result.success}")
    print(f"   Document Type: {result.document_type}")
    print(f"   Confidence: {result.document_type_confidence}")
    print(f"   Text Length: {result.text_length}")
    print(f"   Processing Time: {elapsed:.1f}s")
    
    if result.metadata:
        print(f"   Approval Number: {result.metadata.approval_number}")
        print(f"   Approval Date: {result.metadata.approval_date}")
else:
    print(f"   PDF not found: {pdf_path}")

print("\n" + "=" * 60)
print("If processing time is >10s, LLM is being used")
print("If processing time is <1s, only text extraction is used")
