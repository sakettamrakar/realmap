#!/usr/bin/env python3
"""
Full LLM extraction test on all project PDFs.
"""
import os
import sys
import time
import json

# Set environment before imports
os.environ["MODEL_PATH"] = "C:/models/ai/general/v1/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"
os.environ["GPU_LAYERS"] = "35"
os.environ["CONTEXT_SIZE"] = "8192"
os.environ["LLM_TIMEOUT_SEC"] = "180"

from pathlib import Path

print("=" * 70)
print("FULL LLM EXTRACTION TEST")
print("=" * 70)

# Directory with PDFs
pdf_dir = Path(r"C:\GIT\realmap\outputs\raipur-20\runs\run_20251210_090333_f88ae6\previews\PCGRERA250518000012")

print(f"\nPDF Directory: {pdf_dir}")

# Import extractor
from ai.features.pdf_processing.llm_extractor import LLMExtractor

print("\n1. Initializing LLM Extractor...")
start = time.time()
extractor = LLMExtractor(max_tokens=200)
init_time = time.time() - start
print(f"   Initialized in {init_time:.1f}s")

# Process all PDFs
pdfs = sorted(pdf_dir.glob("*.pdf"))
print(f"\n2. Processing {len(pdfs)} PDFs...")
print("-" * 70)

results = []
total_start = time.time()

for i, pdf in enumerate(pdfs, 1):  # Process ALL PDFs
    print(f"\n[{i}/{len(pdfs)}] {pdf.name}")
    
    pdf_start = time.time()
    result = extractor.process(pdf)
    pdf_time = time.time() - pdf_start
    
    print(f"   Type: {result.document_type.value}")
    print(f"   Confidence: {result.document_type_confidence:.2f}")
    print(f"   Text length: {result.text_length}")
    print(f"   Time: {pdf_time:.1f}s")
    
    if result.metadata.approval_number:
        print(f"   Approval #: {result.metadata.approval_number}")
    if result.metadata.approval_date:
        print(f"   Approval Date: {result.metadata.approval_date}")
    
    results.append({
        "file": pdf.name,
        "type": result.document_type.value,
        "confidence": result.document_type_confidence,
        "text_length": result.text_length,
        "time_sec": pdf_time,
        "approval_number": result.metadata.approval_number,
        "approval_date": result.metadata.approval_date,
    })

total_time = time.time() - total_start

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print(f"\nProcessed: {len(results)} PDFs")
print(f"Total time: {total_time:.1f}s")
print(f"Average time per PDF: {total_time/len(results):.1f}s")

# Count by type
type_counts = {}
for r in results:
    t = r["type"]
    type_counts[t] = type_counts.get(t, 0) + 1

print("\nDocument types found:")
for doc_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {doc_type}: {count}")

# Save results
output_file = Path("outputs/pdf_processing_results.json")
with open(output_file, "w") as f:
    json.dump({
        "total_pdfs": len(results),
        "total_time_sec": total_time,
        "avg_time_per_pdf": total_time / len(results),
        "results": results
    }, f, indent=2)
print(f"\nResults saved to: {output_file}")
