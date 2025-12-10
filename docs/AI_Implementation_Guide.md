# AI Implementation Guide

> **Note:** This guide is the technical execution manual. for the overarching architectural rules, governance policies, and data models, strictly refer to the **[AI Architecture & Governance Blueprint](./AI_Architecture_and_Governance.md)**.

## Navigation
*   [Pre-requisites & Dependencies](#pre-requisites--dependencies)
*   [Versioning](#versioning)
*   [Feature Implementations](#1-ai-powered-project-quality-score)

---

## Pre-requisites & Dependencies

Before starting implementation, ensure your environment matches the **[Architecture Standards](./AI_Architecture_and_Governance.md#8-development-vs-production-guidelines)**.

### System Requirements
*   **Python:** 3.10 or higher
*   **Database:** PostgreSQL 14+ with `pgvector` extension installed.
*   **Hardware (Dev):** NVIDIA GPU with 6GB+ VRAM (Recommended) or Apple Silicon M1/M2/M3.

### Python Dependencies
Add these to your `requirements.txt`:
```text
torch>=2.1.0 --index-url https://download.pytorch.org/whl/cu118
transformers>=4.35.0
accelerate>=0.24.0
llama-cpp-python>=0.2.20  # For GGUF local inference
scikit-learn>=1.3.0
pandas>=2.1.0
opencv-python-headless>=4.8.0 # For Vision/OCR
pypdf>=3.17.0
sentence-transformers>=2.2.2
```

## Versioning
All AI implementations must define a version string constant (e.g., `MODEL_VERSION = "v1.0.0"`) included in all database writes. See **[Governance & Model Lifecycle](./AI_Architecture_and_Governance.md#11-governance--model-lifecycle)**.

---

### 1. AI-powered Project Quality Score

**Goal:**  
Assign a unified 0-100 score to every project to rank quality objectively.

**Governing Policy:**  
See [Scoring Merge Logic](./AI_Architecture_and_Governance.md#5-scoring-merge-logic).

**Required Data:**  
*   `projects` table (amenities list, location coordinates)
*   `developers` table (past track record)
*   `legal_status` (RERA compliance)

**Recommended Model:**  
*   **Weighted Heuristic Engine** (Base Scoring)
*   **Qwen2.5-7B** (Reasoning & Adjustment)

**Implementation Steps:**  
1.  Define weighting logic (e.g., Location=30%, Amenities=20%, Developer=20%, Legal=30%).
2.  Normalize raw data (e.g., standardize amenity counts).
3.  Calculate base score using Python/Pandas.
4.  Feed edge cases to LLM for qualitative adjustment (e.g., "Good developer but has recent active lawsuits").

### PROMPT BLOCK
```python
"""
Implement Project Quality Scoring by:
1. Reading project data from `projects` and `amenities` tables.
2. Calculating a 'Base Score' using weighted sums of:
   - numeric_amenity_score (normalized 0-1)
   - location_prime_score (distance to city center)
   - developer_rank_score (from `developers` table)
3. Using Qwen2.5-7B to generate a human-readable 'Score Reason' string based on the sub-scores.
4. Writing the final `quality_score` and `score_reason` to the `project_scores` table as per the Data Model spec.
5. Creating an API endpoint /scores/update/{project_id} to trigger recalculation.
"""
```

---

### 2. AI-based RERA Document Interpretation

**Goal:**  
Automate the extraction of structured fields from unstructured PDF RERA filings.

**Required Data:**  
*   Raw PDF files stored in S3/Local Storage.

**Recommended Model:**  
*   **Llama-3.2-11B-Vision-Instruct** (Cloud/Local High VRAM) OR **Qwen2.5-7B** with Tesseract OCR (Local Low VRAM).

**Implementation Steps:**  
1.  Ingest PDF and convert pages to images or text.
2.  Process with OCR/Vision model to identify tables (Completion Date, Litigation Lists).
3.  Convert extracted text to JSON schema.
4.  Validate JSON against strict Pydantic models.

### PROMPT BLOCK
```python
"""
Implement RERA PDF Extractor by:
1. Reading PDF files from the /data/rera_docs directory.
2. Converting the first 5 pages to text using Tesseract or `pdfplumber`.
3. Creating a prompt for Qwen2.5-7B to extract:
   - 'Proposed Completion Date'
   - 'Litigation Count'
   - 'Architect Name'
   Output must be strictly valid JSON.
4. Writing the extracted JSON to the `rera_filings` table in Postgres (check Provenance rules).
5. Creating a CLI script `process_rera_docs.py` to batch process new files.
"""
```

---

### 3. AI-powered OCR and Layout Parsing

**Goal:**  
Digitize floor plans to extract room dimensions and configurations.

**Required Data:**  
*   Floor plan images (JPG/PNG).

**Recommended Model:**  
*   **Surya OCR** (Specialized for structure) or **Qwen2.5-VL** (Vision-Language).

**Implementation Steps:**  
1.  Pre-process images (grayscale, contrast boost).
2.  Detect text blocks and geometric shapes using the model.
3.  Associate labels (e.g., "Master Bed") with dimensions (e.g., "12x14").
4.  Store structured room data.

### PROMPT BLOCK
```python
"""
Implement Floor Plan Parser by:
1. Reading image files from `project_gallery` table/storage.
2. Using a vision model to detect text bounding boxes and proximity.
3. Extracting 'Room Name' and 'Dimensions' pairs.
4. Structuring output as a JSON object: { "rooms": [{"name": "Kitchen", "size": "10x8"}] }.
5. Saving this JSON to the `floor_plans` jsonb column in the database.
"""
```

---

### 4. AI-powered Missing Data Imputation

**Goal:**  
Fill critical gaps in the dataset (e.g., missing completion dates) using statistical prediction.

**Governing Policy:**  
See [Imputation Strategy](./AI_Architecture_and_Governance.md#7-imputation-strategy).

**Required Data:**  
*   `projects` table (existing incomplete rows).

**Recommended Model:**  
*   **XGBoost** (tabular imputation) or **Scikit-Learn IterativeImputer**.

**Implementation Steps:**  
1.  Identify columns with 10-40% missingness.
2.  Train a regressor/classifier on complete rows using features like Location, Price, and Developer.
3.  Predict missing values.
4.  Flag imputed values in the database for transparency.

### PROMPT BLOCK
```python
"""
Implement Missing Data Imputer by:
1. Loading the `projects` DataFrame.
2. Identifying missing values in 'possession_year' and 'total_units'.
3. Training an XGBoost regressor using 'location_id', 'developer_id', and 'price_per_sqft' as features.
4. Predicting and filling missing values.
5. Saving results to a new table `projects_imputed` with an `is_imputed` boolean flag.
"""
```

---

### 5. AI-based Price & Area Anomaly Detection

**Goal:**  
Automatically flag erroneous data points entering the pipeline.

**Required Data:**  
*   Incoming scraped data stream.

**Recommended Model:**  
*   **Isolation Forest** (Unsupervised Anomaly Detection).

**Implementation Steps:**  
1.  Fetch recent batch of scraped listings.
2.  Select features: `price`, `area`, `price_per_sqft`.
3.  Run Isolation Forest to detect outliers (e.g., < 1% probability).
4.  Quarantine flagged records for human review.

### PROMPT BLOCK
```python
"""
Implement Price Anomaly Detector by:
1. Fetching all project pricing data.
2. Calculating `price_per_sqft`.
3. Training a Scikit-Learn Isolation Forest on the dataset.
4. Predicting anomaly scores for new incoming rows.
5. If score < -0.5 (anomaly), insert record into `data_quality_flags` table instead of production tables.
"""
```

---

### 6. AI Chat Assistant (Smart Query Engine)

**Goal:**  
Enable natural language search for properties.

**Required Data:**  
*   Vector embeddings of project descriptions and metadata.

**Recommended Model:**  
*   **Qwen2.5-7B-Instruct** (for Query Parsing) + **pgvector** (Postgres Vector Store).

**Implementation Steps:**  
1.  Generate embeddings for all projects (text string of amenities + location).
2.  Store in Postgres using `pgvector`.
3.  On user query, generate query embedding.
4.  Perform cosine similarity search.
5.  Use LLM to synthesize the top 5 results into a natural answer.

### PROMPT BLOCK
```python
"""
Implement Chat Assistant Backend by:
1. Creating a `project_embeddings` table using pgvector.
2. Generating embeddings for all projects using a local SentenceTransformer model.
3. Creating an API endpoint /search/chat that accepts a text query.
4. Converting the user query to an embedding and running a cosine similarity search in Postgres.
5. Returning the top 5 matching project IDs with a summary generated by Qwen2.5.
"""
```

---

### 7. Developer Reputation AI Engine

**Goal:**  
Score developers based on public sentiment and delivery history.

**Required Data:**  
*   News articles, forum posts, consumer complaint databases.

**Recommended Model:**  
*   **DistilBERT** (Sentiment Analysis) or **Qwen2.5-7B** (Contextual extraction).

**Implementation Steps:**  
1.  Scrape/Aggregated text data related to developer names.
2.  Run sentiment analysis to classify snippets as Positive/Negative/Neutral.
3.  Extract specific entities like "Delay", "Fraud", "Quality".
4.  Aggregate into a single "Reputation Score".

### PROMPT BLOCK
```python
"""
Implement Developer Reputation Engine by:
1. Reading scraped text snippets related to developers from the `raw_news` table.
2. Using a pre-trained Sentiment Analysis pipeline (HuggingFace) to score each snippet (-1 to +1).
3. Aggregating scores by `developer_id` to calculate a weighted average.
4. Updating the `developers` table with `reputation_score` and `sentiment_label`.
"""
```

---

### 8. Auto-generated Project Descriptions

**Goal:**  
Create marketing copy for projects that lack descriptions.

**Required Data:**  
*   Project attributes (Location, Amenities, BHK config).

**Recommended Model:**  
*   **Qwen2.5-7B-Instruct-GGUF**.

**Implementation Steps:**  
1.  Construct a prompt with project facts as bullet points.
2.  Ask LLM to write a 150-word engaging summary.
3.  Post-process to remove hallucinations.

### PROMPT BLOCK
```python
"""
Implement Description Generator by:
1. Fetching projects with NULL or empty `description` fields.
2. Formatting project attributes (Name, Locality, Amenities) into a prompt string.
3. Invoking the local Qwen2.5 model to generate a 2-paragraph description.
4. Updating the `projects` table with the generated text.
5. Rate limiting to process 10 projects per minute.
"""
```

---

### 9. Price Trends & Demand Prediction

**Goal:**  
Forecast future pricing to guide users.

**Required Data:**  
*   Historical price points (monthly snapshots).

**Recommended Model:**  
*   **Facebook Prophet** or **ARIMA**.

**Implementation Steps:**  
1.  Aggregate price data by Locality and Month.
2.  Fit time-series model.
3.  Forecast next 6 months.
4.  Store forecast nodes for frontend charting.

### PROMPT BLOCK
```python
"""
Implement Price Forecast Engine by:
1. Querying `historical_prices` table for time-series data grouped by locality.
2. Using the `prophet` library to fit a model for each locality.
3. Generating a 6-month forecast dataframe.
4. Saving forecast points to `locality_price_forecasts` table.
"""
```

---

### 10. Duplicate/Spam Listing Detection

**Goal:**  
Cleanse database of repeated listings.

**Required Data:**  
*   All property listings.

**Recommended Model:**  
*   **TF-IDF** + **Cosine Similarity** (Fast deduplication).

**Implementation Steps:**  
1.  Create text fingerprints for listings (Location + Config + Price range).
2.  Compute similarity matrix.
3.  Cluster items with >95% similarity.
4.  Merge or mark as duplicate.

### PROMPT BLOCK
```python
"""
Implement Duplicate Detector by:
1. Loading active listings into a Pandas DataFrame.
2. Creating a combined text feature column (locality + sqft + price).
3. Calculating cosine similarity between all rows using Scikit-Learn.
4. Identifying pairs with similarity > 0.95.
5. Marking the newer record as `is_duplicate = true` in the database.
"""
```

---

### 11. SEO Auto-generation Engine

**Goal:**  
Automate meta tag creation for thousands of pages.

**Required Data:**  
*   Page context (Project Name, City, Type).

**Recommended Model:**  
*   **Simple Template Engine** (Python f-strings) or **TinyLlama** for variety.

**Implementation Steps:**  
1.  Define templates: "Buy {bhk} Flats in {locality} - {project_name} Reviews".
2.  Use LLM to generate variations for A/B testing.
3.  Write to `page_metadata` table.

### PROMPT BLOCK
```python
"""
Implement SEO Generator by:
1. iterating through all published project pages.
2. Generating a Meta Title (< 60 chars) and Meta Description (< 160 chars) using the project details.
3. Ensuring keywords like 'Price', 'Location', and 'Reviews' are included.
4. Updating the `seo_metadata` table with these tags.
"""
```

---

### 12. AI-based ETL/Pipeline Monitoring

**Goal:**  
Detect breaks in the data collection pipeline.

**Required Data:**  
*   Scraper log stats (rows scraped, error counts).

**Recommended Model:**  
*   **Z-Score / Moving Average** Anomaly Detection.

**Implementation Steps:**  
1.  Track daily scrape volumes.
2.  Calculate moving average (7-day).
3.  Alert if daily volume < (Mean - 2*StdDev).

### PROMPT BLOCK
```python
"""
Implement Pipeline Monitor by:
1. Querying `scrape_logs` for sum of rows added per day.
2. Calculating the 7-day rolling average and standard deviation.
3. Detecting if today's count is more than 2 standard deviations below the mean.
4. Sending a Slack/Email alert via webhook if an anomaly is detected.
"""
```

---

### Recommended Local Model for GTX 1660 Super (6GB VRAM)

**Qwen2.5-7B-Instruct-GGUF (Q4_K_M or Q5_K_S)**  
This fits in 6GB, is fast, highly accurate, and ideal for:
- data analysis
- RERA extraction
- OCR cleanup
- embeddings
- classification
- scoring

**Fallback options:**
- Mistral 7B Instruct GGUF Q4_K_M
- Llama 3.1 8B GGUF Q4_K_M (tight fit but workable)

## Manual QA & Operations

### Manual QA Checklist
| Test Case | Method | Expected Result | Pass/Fail |
|-----------|--------|-----------------|-----------|
| **API Smoke** | `GET /ai/score/project/{id}` | 200 OK + JSON | PENDING |
| **Fallback** | Disable `AI_ENABLED`; Request Score | 200 OK (Null score or fallback msg) | PENDING |
| **UI Listing** | View Project List | Badge shows score/status | PENDING |
| **UI Detail** | View Project Page | "Why this score" visible | PENDING |

### Rollback Procedure
1. **Trigger**: If `ai_error_rate > 5%` or severe UI regression.
2. **Action**:
   - Update `config.yaml`: Set `AI_ENABLED: false`.
   - Restart Service: `sudo systemctl restart realmap-ai`.
   - Verify: Check logs for "AI Disabled" message.
3. **Contact**:
   - On-Call: `pager-ai-squad@example.com`
   - Slack: `#ai-ops-alerts`
