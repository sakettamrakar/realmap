# AI Task Library

**Version:** 1.0  
**Last Updated:** 2025-12-10

This library defines the formal tasks executable by the AI Control Layer.

---

## 1. Core Evaluation Tasks

### `compute_score`
*   **Description:** Calculates the quality score for a project.
*   **Agent:** `scoring_agent`
*   **Input:** `{"project_data": Object, "weights": Object}`
*   **Output:** `{"score": Int, "breakdown": Object}`
*   **Observability:** Metrics: `score_latency`, `score_value_distribution`

### `generate_explanation`
*   **Description:** Generates natural language reason for the score.
*   **Agent:** `scoring_agent`
*   **Input:** `{"score_breakdown": Object, "project_summary": String}`
*   **Output:** `{"explanation": String}`
*   **Observability:** Metrics: `llm_token_count`

---

## 2. Data Processing Tasks

### `normalize_data`
*   **Description:** Standardizes dates, addresses, and enums.
*   **Agent:** `enrichment_agent`
*   **Input:** `{"raw_field": String, "type": String}`
*   **Output:** `{"normalized_value": Any}`
*   **Observability:** Log validation errors.

### `enrich_fields`
*   **Description:** Suggests missing data points based on context.
*   **Agent:** `enrichment_agent`
*   **Input:** `{"partial_record": Object}`
*   **Output:** `{"suggestions": Object}`
*   **Observability:** Track `enrichment_acceptance_rate`

---

## 3. Safety & Integrity Tasks

### `detect_anomalies`
*   **Description:** Scans record for semantic contradictions.
*   **Agent:** `anomaly_detection_agent`
*   **Input:** `{"record": Object}`
*   **Output:** `{"is_anomalous": Boolean, "issues": List}`
*   **Observability:** Alert on HIGH severity.

### `compliance_safety_check`
*   **Description:** Validates LLM output against safety guidelines.
*   **Agent:** `compliance_guard_agent`
*   **Input:** `{"text": String, "source": String}`
*   **Output:** `{"safe": Boolean, "filtered_text": String}`
*   **Observability:** Log rejected content (redacted).

---

## 4. Enhancement Tasks

### `suggest_categories`
*   **Description:** Auto-tags projects with relevant lifestyle categories.
*   **Agent:** `ai_suggestions_agent`
*   **Input:** `{"description": String, "amenities": List}`
*   **Output:** `{"tags": List[String]}`
*   **Observability:** None.

### `rerun_with_local_llm`
*   **Description:** Fallback task to run inference locally if cloud fails (or primary).
*   **Agent:** Any (via `local-llm-adapter`)
*   **Input:** `{"prompt": String, "params": Object}`
*   **Output:** `{"text": String, "usage": Object}`
*   **Observability:** `gpu_memory_usage`, `inference_time`

### `log_metrics`
*   **Description:** Emits telemetry data.
*   **Agent:** System / All
*   **Input:** `{"metric_name": String, "value": Float, "tags": Object}`
*   **Output:** `void`
*   **Observability:** Self-monitoring.
