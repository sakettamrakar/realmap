"""
Comprehensive LLM Extraction Test Script.

Tests each step of LLM extraction and diagnoses issues.
"""
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, r'c:\GIT\realmap')

# Set environment variables BEFORE importing
os.environ['MODEL_PATH'] = r'C:/models/ai/general/v1/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf'
os.environ['CONTEXT_SIZE'] = '8192'  # Increase context size
os.environ['LLM_TIMEOUT_SEC'] = '120'  # Increase timeout

print("=" * 70)
print("LLM EXTRACTION COMPREHENSIVE TEST")
print("=" * 70)

# Check environment
print(f"\n1. Environment Configuration:")
print(f"   MODEL_PATH: {os.environ.get('MODEL_PATH')}")
print(f"   CONTEXT_SIZE: {os.environ.get('CONTEXT_SIZE')}")
print(f"   LLM_TIMEOUT_SEC: {os.environ.get('LLM_TIMEOUT_SEC')}")

# Reload adapter with new settings
print(f"\n2. Loading LLM Adapter...")
import importlib
import ai.llm.adapter as adapter
importlib.reload(adapter)

from ai.llm.adapter import run as llm_run, get_llm_instance, CONTEXT_SIZE

print(f"   Configured CONTEXT_SIZE: {CONTEXT_SIZE}")

llm = get_llm_instance()
print(f"   LLM Loaded: {llm is not None}")

if not llm:
    print("   ERROR: LLM not loaded!")
    sys.exit(1)

# Test PDF
pdf_path = Path(r"c:\GIT\realmap\outputs\raipur-20\runs\run_20251210_090333_f88ae6\previews\PCGRERA250518000012\doc_32_CA_Certificate.pdf")

print(f"\n3. Test PDF: {pdf_path.name}")
print(f"   File size: {pdf_path.stat().st_size:,} bytes")

# Extract text first
print(f"\n4. Extracting text from PDF...")
from pypdf import PdfReader

with open(pdf_path, 'rb') as f:
    reader = PdfReader(f)
    text_parts = []
    for i, page in enumerate(reader.pages[:3]):  # First 3 pages
        page_text = page.extract_text()
        if page_text:
            text_parts.append(f"--- Page {i+1} ---\n{page_text}")
    
    full_text = "\n\n".join(text_parts)
    print(f"   Extracted {len(full_text)} characters from {len(reader.pages)} pages")

# Show text preview
print(f"\n5. Text Preview (first 500 chars):")
print("-" * 50)
print(full_text[:500])
print("-" * 50)

# Test 1: Document Classification
print(f"\n6. Testing Document Classification...")

CLASSIFICATION_PROMPT = """Analyze the following document text and classify it into one of these categories:
- BUILDING_PERMISSION: Building approval, construction permission
- NOC: No Objection Certificate from any authority  
- LAYOUT_PLAN: Layout or site plan approval
- REGISTRATION: Project/company registration certificate
- AGREEMENT: Agreements, MOUs, contracts
- LAND_RECORD: Land ownership documents, property records
- COMPLETION: Completion or occupancy certificate
- ENVIRONMENTAL: Environmental clearance, pollution NOC
- FIRE_SAFETY: Fire department NOC
- FINANCIAL: Bank guarantees, financial documents, CA certificates
- OTHER: Any other document type

Document text (first 2000 characters):
{text}

Respond with ONLY the category name (e.g., "FINANCIAL"), nothing else."""

truncated_text = full_text[:2000]
prompt = CLASSIFICATION_PROMPT.format(text=truncated_text)

print(f"   Prompt length: {len(prompt)} chars")
print(f"   Calling LLM for classification...")

result = llm_run(prompt, max_tokens=50, temperature=0.1)

print(f"\n   Classification Result:")
print(f"   - Raw response: '{result['text']}'")
print(f"   - Tokens used: {result['tokens_used']}")
print(f"   - Latency: {result['latency_ms']}ms")
print(f"   - Error: {result['error']}")

# Parse classification
response_text = result['text'].strip().upper()
print(f"   - Parsed response: '{response_text}'")

# Check if it matches any category
categories = [
    "BUILDING_PERMISSION", "NOC", "LAYOUT_PLAN", "REGISTRATION",
    "AGREEMENT", "LAND_RECORD", "COMPLETION", "ENVIRONMENTAL",
    "FIRE_SAFETY", "FINANCIAL", "OTHER"
]

matched_category = None
for cat in categories:
    if cat in response_text:
        matched_category = cat
        break

print(f"   - Matched category: {matched_category}")

# Test 2: Metadata Extraction
print(f"\n7. Testing Metadata Extraction...")

METADATA_PROMPT = """Extract key information from this financial/CA certificate document.

Document text:
{text}

Extract the following information in JSON format:
{{
    "approval_number": "the certificate/reference number if present",
    "approval_date": "date of issue in YYYY-MM-DD format if present",
    "validity_date": "validity/expiry date in YYYY-MM-DD format if present",
    "issuing_authority": "name of issuing authority/chartered accountant firm",
    "total_cost": numeric value of total project cost if mentioned (number only, no commas),
    "summary": "A one-paragraph summary of the document's key points"
}}

Only include fields where you found reliable information. Use null for missing values.
Return ONLY valid JSON, no explanations or markdown."""

metadata_prompt = METADATA_PROMPT.format(text=full_text[:3000])
print(f"   Prompt length: {len(metadata_prompt)} chars")
print(f"   Calling LLM for metadata extraction...")

result2 = llm_run(metadata_prompt, max_tokens=512, temperature=0.2)

print(f"\n   Metadata Extraction Result:")
print(f"   - Tokens used: {result2['tokens_used']}")
print(f"   - Latency: {result2['latency_ms']}ms")
print(f"   - Error: {result2['error']}")
print(f"\n   - Raw response:")
print("-" * 50)
print(result2['text'][:1000] if result2['text'] else "No response")
print("-" * 50)

# Try to parse JSON
if result2['text']:
    import re
    # Try to find JSON in response
    json_match = re.search(r'\{[\s\S]*\}', result2['text'])
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            print(f"\n   Parsed JSON successfully:")
            for key, value in parsed.items():
                print(f"   - {key}: {value}")
        except json.JSONDecodeError as e:
            print(f"\n   JSON parse error: {e}")
            print(f"   Attempted to parse: {json_match.group()[:200]}...")
    else:
        print(f"\n   No JSON found in response")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Classification: {matched_category or 'FAILED'}")
print(f"Classification latency: {result['latency_ms']}ms")
print(f"Metadata extraction latency: {result2['latency_ms']}ms")
print(f"Total LLM time: {result['latency_ms'] + result2['latency_ms']}ms")
