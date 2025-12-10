# 07 Builder Reputation Prompt

## Role
NLP Engineer.

## Goal
Implement **Developer Reputation AI Engine**. Scrape news/reviews, perform sentiment analysis, and assign a reliability score.

## Inputs
- **Data:** `raw_news_articles`, `consumer_complaints` tables.
- **Model:** `DistilBERT` (Sentiment) + Heuristic Aggregation.

## Outputs
- **Code:** `cg_rera_extractor/ai/scoring/reputation.py`
- **Database:** update `developers.reputation_score`.

## Constraints
- **Bias:** Ensure neutral news doesn't lower score.
- **Privacy:** Anonymize user data if scraping reviews.

## Files to Modify
- `cg_rera_extractor/ai/scoring/reputation.py`

## Tests to Run
- `pytest tests/unit/ai/test_reputation.py`

## Acceptance Criteria
- [ ] Text snippets classified as Pos/Neg/Neutral.
- [ ] Aggregated score calculated (0-10).
- [ ] Developer record updated.

### Example Test
```python
score_builder("Prestige Group", texts=["Delivered on time", "Good quality"])
# Expect score > 8.0
```
