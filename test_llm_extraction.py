"""Test LLM PDF extraction."""
import os
import sys
from pathlib import Path

sys.path.insert(0, r'c:\GIT\realmap')
os.environ['MODEL_PATH'] = r'C:/models/ai/general/v1/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf'

from ai.features.pdf_processing import LLMExtractor, TextExtractor

# Test PDF with good text content
pdf_path = Path(r"c:\GIT\realmap\outputs\raipur-20\runs\run_20251210_090333_f88ae6\previews\PCGRERA250518000012\doc_32_CA_Certificate.pdf")

print(f"Testing on: {pdf_path.name}")
print(f"File size: {pdf_path.stat().st_size:,} bytes")
print()

# First, text extraction for baseline
print("=" * 50)
print("TEXT EXTRACTION (baseline)")
print("=" * 50)
text_extractor = TextExtractor(max_pages=3)
text_result = text_extractor.process(pdf_path)
print(f"Document Type: {text_result.document_type.value}")
print(f"Confidence: {text_result.document_type_confidence:.2f}")
print(f"Text Length: {text_result.text_length}")
print(f"Processing Time: {text_result.processing_time_ms}ms")
if text_result.metadata:
    print(f"Approval Number: {text_result.metadata.approval_number}")
    print(f"Dates: {text_result.metadata.dates[:3] if text_result.metadata.dates else None}")
print()

# Now LLM extraction
print("=" * 50)
print("LLM EXTRACTION")
print("=" * 50)
llm_extractor = LLMExtractor(max_pages=2, max_tokens=512)
llm_result = llm_extractor.process(pdf_path)
print(f"Document Type: {llm_result.document_type.value}")
print(f"Confidence: {llm_result.document_type_confidence:.2f}")
print(f"Text Length: {llm_result.text_length}")
print(f"Processing Time: {llm_result.processing_time_ms}ms")
if llm_result.metadata:
    print(f"Approval Number: {llm_result.metadata.approval_number}")
    print(f"Approval Date: {llm_result.metadata.approval_date}")
    print(f"Issuing Authority: {llm_result.metadata.issuing_authority}")
    print(f"Summary: {llm_result.metadata.summary[:200] if llm_result.metadata.summary else None}...")
print()

print("=" * 50)
print("COMPARISON")
print("=" * 50)
print(f"Text extraction: {text_result.processing_time_ms}ms")
print(f"LLM extraction:  {llm_result.processing_time_ms}ms")
print(f"LLM is {llm_result.processing_time_ms / max(text_result.processing_time_ms, 1):.1f}x slower")
