# AI Architecture & Governance Blueprint

**Status:** Draft / Active  
**Version:** 1.0  
**Related Documents:**  
- [AI Features Overview](./AI_Features.md)  
- [AI Implementation Guide](./AI_Implementation_Guide.md)

---

## 1. Architecture Overview

 The `realmap` AI ecosystem operates as a modular "Sidecar" service, loosely coupled with the primary Backend API. This ensures that heavy AI computation does not block the main user-facing application.

### System Diagram

```mermaid
graph TD
    User[User / Client] -->|Requests| API[Core Backend API]
    API -->|Read/Write| DB[(Postgres DB)]
    
    subgraph "AI Microservice Layer"
        Scheduler[Task Scheduler]
        Inference[Inference Engine (Local/LLM)]
        Monitor[Drift Monitor]
    end

    Scheduler -->|Trigger| Inference
    Inference -->|Read Context| DB
    Inference -->|Write Results + Audit| DB
    Monitor -->|Check Stats| DB
```

## 2. Microservice Design

*   **Service Isolation:** The AI Logic resides in a dedicated Python package `cg_rera_extractor.ai` or a separate microservice container (e.g., FastAPI app on port 8001).
*   **Interface:** Communication occurs via internal REST APIs or direct DB access (for batch jobs).
*   **Hardware Agnostic:** Designed to run on CPU (Production/Cloud) or GPU (Local Dev/Training).

## 3. Data Models

To support AI features, the database schema must handle probabilistic data, not just deterministic facts.

### 3.1 AI Scoring Tables (`project_ai_scores`)
| Column | Type | Description |
| :--- | :--- | :--- |
| `project_id` | UUID | Foreign Key to Projects |
| `quality_score` | FLOAT | 0-100 Aggregate Score |
| `sub_scores` | JSONB | `{ "location": 85, "amenities": 40, "legal": 90 }` |
| `explanation` | TEXT | AI-generated reasoning string |
| `model_version` | TEXT | E.g., "qwen2.5-7b-v1" |
| `updated_at` | TIMESTAMP | Last calculation time |

### 3.2 Provenance & Audit Logs (`ai_provenance_log`)
Every AI modification to the database is tracked.
| Column | Type | Description |
| :--- | :--- | :--- |
| `entity_type` | VARCHAR | "project", "developer", "listing" |
| `entity_id` | UUID | Target record ID |
| `field_changed` | VARCHAR | E.g., "possession_date" |
| `old_value` | JSONB | Previous value |
| `new_value` | JSONB | AI predicted value |
| `confidence` | FLOAT | 0.0 - 1.0 |
| `is_human_verified` | BOOLEAN | False by default |

## 4. Provenance & Auditability

**Rule:** No AI data enters the system without a "Source of Truth" tag.
*   **Raw Data:** Tagged as `source: scraper` or `source: rera`.
*   **AI Data:** Tagged as `source: ai_imputed` or `source: ai_prediction`.
*   **Audit Trail:** Users must be able to trace a score back to the specific inputs and model version that generated it.

## 5. Scoring Merge Logic

When combining Heuristic (Rule-based) scores with AI Scored adjustments:
1.  **Base Layer:** Calculate strict rule-based score (deterministic).
2.  **Adjustment Layer:** AI provides a +/- multiplier based on qualitative factors (sentiment, photos).
3.  **Final Score:** `Final = (Base * 0.7) + (AI_Adjustment * 0.3)`.

## 6. Priority & Conflict Resolution Rules

When data conflicts arise, the following hierarchy applies:
1.  **Admin Override:** Explicit manual entry by staff.
2.  **RERA Document:** Official government filing data.
3.  **Developer Website:** Direct source.
4.  **AI High Confidence (>90%):** Strong pattern match.
5.  **Aggregator Listings:** Housing/99acres scrapings.
6.  **AI Low Confidence (<70%):** Marked as "Estimate" in UI.

## 7. Imputation Strategy

See [Feature #4](./AI_Features.md#4-ai-powered-missing-data-imputation).
*   **Threshold:** Do NOT impute if >50% of row data is missing.
*   **Flagging:** All imputed fields must be visibly flagged in the internal dashboard.
*   **Re-validation:** Imputed values are re-checked nightly against new incoming real data.

## 8. Development vs. Production Guidelines

### Local Development (The "Lab")
*   **Hardware:** GTX 1660 Super (6GB VRAM).
*   **Model:** Qwen2.5-7B (4-bit quantized).
*   **Focus:** Experimentation, prompt tuning, small batch validation.

### Production Deployment (The "Factory")
*   **Hardware:** CPU instances (Cost-effective) or Serverless GPU (Modal/RunPod) for on-demand bursts.
*   **Model:** ONNX runtime for classical ML, or API calls to optimized LLM endpoints if local inference is too slow.
*   **Focus:** Reliability, latency, throughput.

## 9. Scheduling & Orchestration

*   **Real-time (Synchronous):**
    *   Chat Assistant (Feature #6).
    *   Feature: User expects < 2s response.
*   **Near Real-time (Async Queue):**
    *   OCR & RERA Parsing (Features #2, #3).
    *   Triggered on file upload. Processed via Celery/RabbitMQ.
*   **Nightly Batch (Cron):**
    *   Scoring Updates, Price Trends (Features #1, #9).
    *   Heavy recalculation when system load is low.

## 10. Explainability (XAI) Requirements

*   **"Why this score?"**: Every score must include a generated sentence explaining the primary drivers (e.g., "High score due to metro proximity (500m) and Grade A builder").
*   **Confidence Intervals**: Price predictions must show a range (e.g., "₹1.2Cr - ₹1.35Cr"), not a single point.

## 11. Governance & Model Lifecycle

1.  **Staging:** Models are tested on a "Golden Dataset" (manually verified records).
2.  **Promotion:** Only models improving accuracy on the Golden Set are promoted to Prod.
3.  **Versioning:** All rows in DB generated by AI track `model_version`. If a model is found defective, we can rollback specific version updates.

## 12. Monitoring & Drift Detection

See [Feature #12](./AI_Features.md#12-ai-based-etlpipeline-monitoring).
*   **Data Drift:** Alert if input distribution shifts (e.g., sudden drop in average price).
*   **Concept Drift:** Alert if model accuracy degrades over time.
*   **Pipeline Health:** Monitor success/failure rates of AI jobs.

## 13. API Contracts

**Request (Standard AI Task):**
```json
POST /api/ai/task/analyze-project
{
  "project_id": "uuid",
  "task_type": "quality_score",
  "config": { "retries": 3 }
}
```

**Response:**
```json
{
  "status": "success",
  "data": { "score": 88, "reason": "..." },
  "metadata": { "model": "qwen2.5", "latency_ms": 450 }
}
```

## 14. Migration Plan

*   **Phase 1 (Non-Destructive):** Deploy AI features that *add* data (Descriptions, SEO) without overwriting core fields.
*   **Phase 2 (Parallel):** Run Scoring and OCR in "Shadow Mode" (logging results but not showing to users).
*   **Phase 3 (Live):** Enable user-facing AI features and imputation.

## 15. Operational Checklist

- [ ] **Daily:** Check `ai_provenance_log` for anomalies.
- [ ] **Weekly:** Review specific "Low Confidence" flagged rows.
- [ ] **Monthly:** Re-run Golden Dataset tests against current model.
- [ ] **Quarterly:** Re-evaluate Model Landscape (e.g., Switch from Qwen to Llama 4 if better).
