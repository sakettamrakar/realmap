# 10 Duplicate Detection Prompt

## Role
Data Engineer.

## Goal
Implement **Duplicate/Spam Listing Detection**. Identify identical property listings from different sources.

## Inputs
- **Data:** All active listings.
- **Algorithm:** TF-IDF + Cosine Similarity (Scikit-Learn).

## Outputs
- **Code:** `cg_rera_extractor/ai/cleaning/dedupe.py`
- **Database:** Mark `is_duplicate=True` on redundant rows.

## Constraints
- **Threshold:** Similarity > 0.95.
- **Preserve:** Keep the oldest or most complete record as master.

## Files to Modify
- `cg_rera_extractor/ai/cleaning/dedupe.py`

## Tests to Run
- `pytest tests/unit/ai/test_dedupe.py`

## Acceptance Criteria
- [ ] Identical text listings flagged.
- [ ] Slightly modified listings (diff price) grouped.
- [ ] DB updated correctly.

### Example Test
```bash
python scripts/run_dedupe.py
```
