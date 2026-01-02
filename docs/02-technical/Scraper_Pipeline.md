# Scraper & ETL Pipeline

**Version:** 1.0.0
**Date:** 2025-12-12

---

## 1. Scraper Engine

The scraper is a **Playwright** based CLI tool. It mimics a human user to navigate the RERA portal, solving pagination and extracting data from dynamic forms.

### Modes
*   **`FULL`**: Scrapes every project found. Best for initial hydration.
*   **`DELTA`**: Skips projects that are already in the cache. Best for nightly updates.
    *   *Cache File:* `data/scraped_cache.json`

### Configuration
Config is managed via YAML (e.g., `config.yaml`):
```yaml
run:
  mode: FULL # or DELTA
  headless: true
  max_listings: 100
db:
  url: "postgresql://user:pass@localhost:5432/realmap"
```

### Running the Scraper
```bash
python -m cg_rera_extractor.cli run --config config.yaml
```

---

## 2. Ingestion Pipeline

### Step 1: Parsing
Raw HTML is parsed into "Sections" (e.g., "Promoter Details"), then mapped to the **V1 Schema** using a robust key-variant matching system (`logical_sections_and_keys.json`).

### Step 2: Validation (QA)
Before database insertion, data is validated:
*   **Price Sanity:** Flags outliers (< ₹100/sqft).
*   **Geo Bounds:** Flags coordinates outside Chhattisgarh.

### Step 3: Loading
The `loader` module inserts validated JSON into PostgreSQL.
```bash
python tools/load_run_into_db.py --run-dir outputs/runs/latest
```

### Step 4: PDF Processing (NEW)
After database loading, PDF documents are processed to extract additional structured data:
```bash
# Process all PDFs from scraped runs
python tools/process_pdfs.py --page 1
```

The PDF processing pipeline:
1. **OCR:** Converts PDF pages to images and extracts text (Tesseract/EasyOCR)
2. **Classification:** Identifies document type from 11 categories
3. **LLM Extraction:** Extracts structured fields using Qwen2.5-7B
4. **Merging:** Combines with scraped data to create enriched V2 JSON

See [PDF Processing Documentation](./orchestration/pdf-processing.md) for details.

---

## 3. Enrichment Pipelines

### Geocoding
*   **Tool:** `geocode_projects.py`
*   **Logic:**
    1.  Normalize address string (District -> Tehsil).
    2.  Query Nominatim/Google APIs.
    3.  Save result to `latitude`/`longitude`.

### Amenity Scoring
*   **Tool:** `compute_project_scores.py`
*   **Logic:**
    1.  Fetch Schools/Hospitals in 2km radius.
    2.  Calculate weighted score (0-100).
    3.  Update `project_scores` table.

---

## 4. Troubleshooting
*   **CAPTCHA Failures:** The scraper pauses and alerts the user if a CAPTCHA is detected. Manual intervention (in header mode) may be needed.
*   **Selector Drift:** If RERA changes their HTML, update selectors in `selectors.yaml` or `raw_extractor.py`.

---

## 5. Related Documents
- [Architecture](./Architecture.md)
- [Data Model](./Data_Model.md)
