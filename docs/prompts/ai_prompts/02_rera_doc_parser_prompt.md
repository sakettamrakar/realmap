# 02 RERA Doc Parser Prompt

## Role
Senior Python ML Engineer (OCR Specialist).

## Goal
Implement **AI-based RERA Document Interpretation**. A pipeline to ingest PDF files, extract structured fields (Completion Date, Litigation Count), and store them.

## Inputs
- **Files:** Unstructured PDFs in `/data/raw_rera_docs/`.
- **Libraries:** `pdf2image`, `pytesseract` (or `surya-ocr`), `transformers`.

## Outputs
- **Code:** `cg_rera_extractor/ai/parsing/rera_pdf_parser.py`
- **Database:** `rera_filings` table (new columns for extracted data).

## Constraints
- **Resource Limits:** PDF processing is heavy; use async queue (Celery/BackgroundTasks).
- **Safety:** Tag extracted data with `source='ai_ocr'`.
- **Accuracy:** If OCR confidence < 70%, flag field as `requires_human_review`.

## Files to Modify
- `cg_rera_extractor/ai/parsing/rera_pdf_parser.py`
- `cg_rera_extractor/tasks/queue.py`

## Tests to Run
- `pytest tests/unit/ai/test_pdf_parser.py`

## Acceptance Criteria
- [ ] System accepts a PDF path.
- [ ] Text is extracted from first 5 pages.
- [ ] LLM (Qwen) correctly identifies "Proposed Completion Date" from the messy text.
- [ ] Valid JSON is written to DB.

### Example Test
```bash
python scripts/test_ocr.py --file "sample_rera.pdf"
# Expect JSON output printed to console with 'completion_date' YYYY-MM-DD.
```
