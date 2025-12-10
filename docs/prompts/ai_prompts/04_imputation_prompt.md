# 04 Imputation Prompt

## Role
Data Scientist.

## Goal
Implement **AI-powered Missing Data Imputation**. Fill gaps in `possession_year` and `total_units` using regression/classification based on similar projects.

## Inputs
- **Database:** `projects` table (Training set: rows with complete data).
- **Library:** `scikit-learn` (XGBoost / IterativeImputer).

## Outputs
- **Code:** `cg_rera_extractor/ai/analytics/imputer.py`
- **Database:** `projects` (rows updated, `is_imputed` flag set).

## Constraints
- **Threshold:** Do not impute if >50% columns missing.
- **Flagging:** MUST set `source_type='ai_imputed'` for auditing.

## Files to Modify
- `cg_rera_extractor/ai/analytics/imputer.py`
- `scripts/run_imputation.py`

## Tests to Run
- `pytest tests/unit/ai/test_imputer.py`

## Acceptance Criteria
- [ ] Model trains on existing data (min 100 samples).
- [ ] Predicts `possession_year` within +/- 2 years accuracy.
- [ ] Updates DB correctly without overwriting 'RERA' sourced data.

### Example Test
```bash
python scripts/run_imputation.py --dry-run
# Shows diff of what would be changed.
```
