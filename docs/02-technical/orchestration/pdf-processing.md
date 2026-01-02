# PDF Processing Pipeline

## Overview

The PDF processing pipeline extracts structured data from RERA PDF documents using OCR and LLM technology.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PDF Processing Pipeline                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   PDF File   │───▶│ PDF Converter│───▶│   Images     │                  │
│  │  (input)     │    │ (pdf2image)  │    │ (per page)   │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                 │                           │
│                                                 ▼                           │
│                                          ┌──────────────┐                  │
│                                          │  OCR Engine  │                  │
│                                          │ (Tesseract/  │                  │
│                                          │  EasyOCR)    │                  │
│                                          └──────────────┘                  │
│                                                 │                           │
│                                                 ▼                           │
│                                          ┌──────────────┐                  │
│                                          │ Text Cleaner │                  │
│                                          │ (normalize)  │                  │
│                                          └──────────────┘                  │
│                                                 │                           │
│                                                 ▼                           │
│  ┌──────────────┐                        ┌──────────────┐                  │
│  │   Document   │◀───────────────────────│  Classifier  │                  │
│  │     Type     │                        │ (11 types)   │                  │
│  └──────────────┘                        └──────────────┘                  │
│         │                                       │                           │
│         ▼                                       ▼                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Prompt     │───▶│ LLM Extractor│───▶│  Structured  │                  │
│  │  Template    │    │ (Qwen2.5-7B) │    │    Data      │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                 │                           │
│                                                 ▼                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  Scraped     │───▶│ Data Merger  │───▶│  Enriched    │                  │
│  │  Metadata    │    │ (resolve     │    │  JSON (V2)   │                  │
│  │  (V1 JSON)   │    │  conflicts)  │    │              │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Module Structure

```
cg_rera_extractor/
├── __init__.py           # Package exports
├── ocr/                   # OCR processing
│   ├── __init__.py
│   ├── ocr_config.py     # Configuration settings
│   ├── pdf_converter.py  # PDF to image conversion
│   ├── ocr_engine.py     # Text extraction (Tesseract/EasyOCR)
│   └── text_cleaner.py   # Text normalization
├── extraction/            # LLM extraction
│   ├── __init__.py
│   ├── document_classifier.py  # Document type classification
│   ├── llm_extractor.py       # LLM-based extraction
│   ├── schemas/               # Pydantic schemas per doc type
│   │   ├── base.py
│   │   ├── registration_certificate.py
│   │   ├── layout_plan.py
│   │   └── ... (8 schemas)
│   └── prompts/               # LLM prompts per doc type
│       ├── registration_certificate.txt
│       ├── layout_plan.txt
│       └── ... (prompts)
├── enrichment/            # Data merging
│   ├── __init__.py
│   ├── conflict_resolver.py  # Handle data conflicts
│   └── data_merger.py        # Merge scraped + extracted
└── runs/                  # Orchestration
    ├── __init__.py
    └── pdf_processor.py   # Main processing orchestrator
```

## Document Types Supported

| Type | Description | Key Fields |
|------|-------------|------------|
| `registration_certificate` | RERA registration | reg_number, project_name, promoter |
| `layout_plan` | Plot layouts | total_area, plots, open_spaces |
| `bank_passbook` | Financial records | bank_name, account_number, balance |
| `encumbrance_certificate` | Ownership status | property_id, encumbrances |
| `sanctioned_plan` | Approved building plans | sanction_number, floor_count |
| `completion_certificate` | Project completion | completion_date, certificate_no |
| `building_plan` | Structural drawings | floors, built_up_area |
| `noc_document` | No Objection Certificates | issuing_authority, validity |

## Usage

### CLI Tool

```bash
# Process a single run directory
python tools/process_pdfs.py --run-dir outputs/parallel-page1/runs/run_001

# Process all runs from page 1
python tools/process_pdfs.py --page 1

# Process multiple pages
python tools/process_pdfs.py --pages 1,2,3,4,5

# Process specific document types only
python tools/process_pdfs.py --page 1 --doc-types registration_certificate,layout_plan

# Process without LLM (OCR text extraction only)
python tools/process_pdfs.py --page 1 --no-llm

# Save intermediate OCR text files for debugging
python tools/process_pdfs.py --page 1 --save-ocr

# Verbose logging
python tools/process_pdfs.py --page 1 --verbose
```

### Python API

```python
from cg_rera_extractor import PDFProcessor, OCRConfig

# Configure OCR
config = OCRConfig(
    dpi=300,
    languages=["eng", "hin"],
)

# Initialize processor
processor = PDFProcessor(
    ocr_config=config,
    enable_llm=True,
    save_intermediate=False,
)

# Process a run directory
result = processor.process_run_directory(
    "outputs/parallel-page1/runs/run_001"
)

print(f"Project: {result.project_id}")
print(f"Documents processed: {result.documents_processed}")
print(f"Successful: {result.documents_successful}")
print(f"Output: {result.output_path}")

# Check individual document results
for doc_result in result.document_results:
    print(f"  {doc_result.document_path}: {doc_result.document_type.value}")
    if doc_result.extracted_data:
        print(f"    Confidence: {doc_result.confidence:.2f}")
```

## Output Schema

The enriched JSON (V2) includes:

```json
{
  "project_id": "CGRERA/...",
  "project_name": "...",
  "promoter_name": "...",
  
  "pdf_extractions": {
    "registration_certificate": {
      "registration_number": "...",
      "issue_date": "...",
      "validity_date": "..."
    },
    "layout_plan": {
      "total_area": "...",
      "plot_count": 25
    }
  },
  
  "_enrichment": {
    "version": "2.0",
    "processed_at": "2024-12-14T...",
    "fields_updated": 5,
    "fields_added": 12,
    "conflicts_resolved": 2
  }
}
```

## System Requirements

### Python Dependencies

```bash
pip install -r requirements-pdf.txt
```

### System Dependencies

**Windows:**
```powershell
choco install tesseract
choco install poppler
```

**Ubuntu/Debian:**
```bash
sudo apt install tesseract-ocr tesseract-ocr-hin
sudo apt install poppler-utils
```

**macOS:**
```bash
brew install tesseract tesseract-lang
brew install poppler
```

## Configuration

### Environment Variables

```bash
# LLM Configuration
MODEL_PATH=./models/qwen2.5-7b-instruct-q4_k_m.gguf
GPU_LAYERS=33

# Enable AI features
AI_ENABLED=true
AI_SCORE_ENABLED=true
```

### OCR Configuration

```python
from cg_rera_extractor.ocr import OCRConfig

config = OCRConfig(
    dpi=300,                    # PDF conversion DPI
    languages=["eng", "hin"],   # OCR languages
    use_easyocr_fallback=True,  # Fallback to EasyOCR
    preprocess=True,            # Apply image preprocessing
    confidence_threshold=0.5,   # Minimum OCR confidence
)
```

## Workflow Integration

The PDF processing pipeline integrates with the existing scraping workflow:

1. **Scraping (Step 1)**: `tools/parallel_scrape.py` scrapes project data
2. **Database Load**: `tools/load_runs_to_db.py` loads scraped data
3. **PDF Download**: `download_pdfs.py` downloads PDF documents
4. **PDF Processing**: `tools/process_pdfs.py` extracts structured data ← **NEW**
5. **AI Scoring**: `tools/process_all_listings.py` generates investment scores

## Troubleshooting

### OCR Quality Issues

- Increase DPI: `--dpi 400`
- Check language packs installed
- Enable preprocessing: `OCRConfig(preprocess=True)`

### LLM Extraction Failures

- Verify model file exists at MODEL_PATH
- Check GPU memory (requires ~6GB VRAM)
- Try smaller model or disable GPU: `GPU_LAYERS=0`

### Missing Dependencies

```bash
# Check Tesseract
tesseract --version

# Check Poppler
pdfinfo --version

# Check Python packages
pip list | grep -E "pdf2image|pytesseract|easyocr"
```
