# 12 ETL Monitoring Prompt

## Role
SRE / DevOps.

## Goal
Implement **AI-based ETL/Pipeline Monitoring**. Detect scraper failures via statistical anomaly detection on volume.

## Inputs
- **Data:** `scrape_logs` (Date, Rows Added).
- **Algorithm:** Z-Score (Rolling Average).

## Outputs
- **Code:** `cg_rera_extractor/ops/monitor.py`
- **Alerts:** Slack Webhook / Email.

## Constraints
- **False Positives:** Tune sensitivity (Sigma=2 or 3).

## Files to Modify
- `cg_rera_extractor/ops/monitor.py`

## Tests to Run
- `pytest tests/unit/ops/test_monitor.py`

## Acceptance Criteria
- [ ] Z-score calculated correctly.
- [ ] Alert triggered when volume drops to 0.

### Example Test
```bash
python scripts/check_pipeline.py
```
