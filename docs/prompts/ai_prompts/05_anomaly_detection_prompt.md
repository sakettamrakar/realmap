# 05 Anomaly Detection Prompt

## Role
Data Engineer.

## Goal
Implement **AI-based Price & Area Anomaly Detection**. Flag unrealistic data (e.g., price ₹10) before it corrupts the UI.

## Inputs
- **Data Stream:** Incoming scraped projects (dicts).
- **Model:** `IsolationForest` (trained on historical valid prices).

## Outputs
- **Code:** `cg_rera_extractor/ai/analytics/anomaly_detector.py`
- **Database:** `data_quality_flags` table.

## Constraints
- **Latency:** Must run fast (<10ms) per record during ingestion.
- **Action:** If anomaly score > threshold, soft-delete or flag; do not discard silently.

## Files to Modify
- `cg_rera_extractor/db/loader.py` (Integration point)
- `cg_rera_extractor/ai/analytics/anomaly_detector.py`

## Tests to Run
- `pytest tests/unit/ai/test_anomaly.py`

## Acceptance Criteria
- [ ] Detector identifies a ₹500/sqft property in a ₹10,000/sqft zone as anomalous.
- [ ] Flag is persisted to DB.
- [ ] Ingestion pipeline does not crash.

### Example Test
```python
detector.check({"price": 100, "area": 1000}) # Should return IS_ANOMALY=True
```
