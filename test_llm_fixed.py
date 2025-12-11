#!/usr/bin/env python3
"""
Test LLM extraction with optimized prompts.
"""
import os
import sys
import time

# Set environment before imports
os.environ.setdefault("MODEL_PATH", "C:/models/ai/general/v1/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf")
os.environ.setdefault("GPU_LAYERS", "35")  # Use GPU
os.environ.setdefault("CONTEXT_SIZE", "8192")
os.environ.setdefault("LLM_TIMEOUT_SEC", "180")  # 3 minutes

from pathlib import Path

print("=" * 70)
print("LLM EXTRACTION TEST - GPU ACCELERATED")
print("=" * 70)

# Test file
pdf_path = Path(r"C:\GIT\realmap\outputs\raipur-20\runs\run_20251210_090333_f88ae6\previews\PCGRERA250518000012\doc_32_CA_Certificate.pdf")

if not pdf_path.exists():
    print(f"ERROR: PDF not found: {pdf_path}")
    sys.exit(1)

print(f"\n1. Test PDF: {pdf_path.name}")
print(f"   File size: {pdf_path.stat().st_size:,} bytes")

# Load LLM adapter
print("\n2. Loading LLM adapter...")
from ai.llm.adapter import run as llm_run, get_llm_instance, LLM_TIMEOUT_SEC
print(f"   Timeout: {LLM_TIMEOUT_SEC}s")

llm = get_llm_instance()
if llm is None:
    print("   ERROR: LLM failed to load")
    sys.exit(1)
print("   LLM loaded successfully")

# Extract text
print("\n3. Extracting text from PDF...")
from pypdf import PdfReader
reader = PdfReader(str(pdf_path))
text = ""
for page in reader.pages[:4]:
    text += page.extract_text() + "\n"
print(f"   Extracted {len(text)} characters")

# Test classification
print("\n4. Testing classification...")
from ai.features.pdf_processing.llm_extractor import DOCUMENT_CLASSIFICATION_PROMPT

class_prompt = DOCUMENT_CLASSIFICATION_PROMPT.format(text=text[:2000])
print(f"   Prompt length: {len(class_prompt)} chars")

start = time.time()
result = llm_run(class_prompt, max_tokens=50, temperature=0.1)
elapsed = time.time() - start

print(f"   Response: {repr(result['text'])}")
print(f"   Time: {elapsed:.1f}s")
print(f"   Error: {result.get('error')}")

# Test metadata extraction with new optimized prompt
print("\n5. Testing metadata extraction (optimized prompt)...")
from ai.features.pdf_processing.llm_extractor import METADATA_EXTRACTION_PROMPT

meta_prompt = METADATA_EXTRACTION_PROMPT.format(
    document_type="FINANCIAL",
    text=text[:3000]
)
print(f"   Prompt length: {len(meta_prompt)} chars")

start = time.time()
result = llm_run(
    meta_prompt,
    system="Extract info as JSON.",
    max_tokens=256,
    temperature=0.1
)
elapsed = time.time() - start

print(f"   Response: {repr(result['text'][:500])}")
print(f"   Time: {elapsed:.1f}s")
print(f"   Error: {result.get('error')}")

# Try to parse JSON
print("\n6. Parsing JSON response...")
import re
import json

response = result.get('text', '')
json_match = re.search(r'\{[\s\S]*\}', response)
if json_match:
    try:
        data = json.loads(json_match.group())
        print("   Parsed successfully!")
        for key, value in data.items():
            if value:
                print(f"   - {key}: {value}")
    except json.JSONDecodeError as e:
        print(f"   JSON parse error: {e}")
        print(f"   Raw JSON: {json_match.group()}")
else:
    print("   No JSON found in response")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
