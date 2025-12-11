#!/usr/bin/env python3
"""
Find PDFs with extractable text.
"""
import os
from pathlib import Path

os.environ["MODEL_PATH"] = "C:/models/ai/general/v1/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"
os.environ["GPU_LAYERS"] = "35"

pdf_dir = Path(r"C:\GIT\realmap\outputs\raipur-20\runs\run_20251210_090333_f88ae6\previews\PCGRERA250518000012")

from pypdf import PdfReader

print("PDFs with extractable text:")
print("-" * 60)

best_pdf = None
best_chars = 0

for pdf in sorted(pdf_dir.glob("*.pdf")):
    try:
        reader = PdfReader(str(pdf))
        text = ""
        for page in reader.pages[:3]:
            text += page.extract_text() or ""
        
        chars = len(text)
        if chars > 100:
            print(f"{pdf.name}: {chars} chars")
            if chars > best_chars:
                best_chars = chars
                best_pdf = pdf
    except Exception as e:
        print(f"{pdf.name}: ERROR - {e}")

print("-" * 60)
if best_pdf:
    print(f"\nBest candidate: {best_pdf.name} ({best_chars} chars)")
    print(f"\nFirst 500 chars of text:")
    reader = PdfReader(str(best_pdf))
    text = reader.pages[0].extract_text() or ""
    print(text[:500])
