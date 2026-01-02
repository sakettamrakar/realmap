# AI Implementation Guide

**Version:** 1.0.0
**Date:** 2025-12-12

---

## 1. Architecture & Stack
*   **Language:** Python 3.10+
*   **Orchestration:** FastAPI + Task Scheduler
*   **Database:** PostgreSQL with **pgvector** extension
*   **Models:**
    *   **Vector:** `sentence-transformers/all-MiniLM-L6-v2`
    *   **LLM:** `Qwen2.5-7B-Instruct` (Local/GGUF) or OpenAI GPT-4o (Cloud fallback)

---

## 2. Setup & Configuration

### Prerequisites
1.  **GPU (Optional):** NVIDIA GTX 1660 Ti (6GB VRAM) recommended for local inference.
2.  **Environment Variables:**
    ```ini
    AI_ENABLED=true
    MODEL_PATH=./models/qwen2.5-7b-instruct-q4_k_m.gguf
    LLM_TIMEOUT_SEC=60
    ```

### Running the AI Service
The AI service runs as a separate process or module:
```bash
# Start the AI Microservice
uvicorn ai.main:app --host 0.0.0.0 --port 8001
```

---

## 3. Core Implementation Modules

### 3.1 Quality Scoring (`ai/scoring/`)
*   **Logic:** Weighted heuristic (Location=30%, Amenities=20%) + LLM adjustment for edge cases.
*   **Trigger:** Nightly batch or Manual `POST /ai/score/project/{id}`.
*   **Output:** Updates `project_scores` table.

### 3.2 Chat Assistant (`ai/chat/`)
*   **Vector Store:** Projects are vectorized (Desc + Location + Amenities) and stored in `project_embeddings`.
*   **Flow:**
    1.  User Query -> Embedding.
    2.  `SELECT * FROM project_embeddings ORDER BY embedding <=> query_embedding LIMIT 5`.
    3.  LLM Synthesizes stats of top 5 projects into a friendly answer.

### 3.3 Anomaly Detection (`ai/anomaly/`)
*   **Logic:** Isolation Forest (Scikit-Learn) to detect price/sqft outliers.
*   **Action:** Rows with high anomaly scores are flagged in `qa_flags` and excluded from search index.

### 3.4 PDF Processing (`cg_rera_extractor/ocr/`, `cg_rera_extractor/extraction/`)
A complete OCR + LLM pipeline for extracting structured data from RERA PDF documents.

*   **OCR Engine:** Tesseract (primary) + EasyOCR (fallback) for Hindi/English text.
*   **Document Types:** 11 supported types including Registration Certificate, Layout Plan, Bank Passbook, etc.
*   **LLM Extraction:** Uses Qwen2.5-7B with document-specific prompts to extract structured fields.
*   **Data Merging:** Combines OCR extractions with scraped metadata, resolving conflicts.

```bash
# Process PDFs for a specific page
python tools/process_pdfs.py --page 1

# Process with specific document types
python tools/process_pdfs.py --page 1 --doc-types registration_certificate,layout_plan
```

See [PDF Processing Documentation](../02-technical/orchestration/pdf-processing.md) for full details.

---

## 4. Agent Control Layer
The system uses specialized "Agents" for different tasks:
*   **Scoring Agent:** Calculates and explains scores.
*   **Compliance Agent:** Checks for regulatory red flags.
*   **Enrichment Agent:** Infers missing attributes (e.g., "Gym" implies "Lifestyle").

New agents are defined in `ai/agents/{agent_name}.json`.

---

## 5. Operations & Runbook

### Health Check
```http
GET /ai/health
=> { "status": "ok", "model_loaded": "qwen2.5" }
```

### Common Issues
*   **OOM (Out of Memory):** If using local LLM, ensure no other heavy GPU processes are running. Reduce context window if needed.
*   **Timeout:** PDF parsing can be slow. Increase `LLM_TIMEOUT_SEC` for document tasks.
*   **Drift:** If scores look wrong, re-run the "Golden Dataset" validation script: `python -m ai.tools.validate_model`.

---

## 6. Related Documents
- [AI Overview](./AI_Overview.md)
- [API Reference](../02-technical/API_Reference.md)
