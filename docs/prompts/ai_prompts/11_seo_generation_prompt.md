# 11 SEO Generation Prompt

## Role
SEO Specialist / Engineer.

## Goal
Implement **SEO Auto-generation Engine**. Bulk create meta titles/descriptions.

## Inputs
- **Data:** Project Name, Locality, Property Type.
- **Model:** Python `f-strings` (Template) or Small LLM.

## Outputs
- **Code:** `cg_rera_extractor/ai/gen/seo.py`
- **Database:** `seo_metadata` table.

## Constraints
- **Length:** Title < 60 chars, Desc < 160 chars.
- **Uniqueness:** Unique per page.

## Files to Modify
- `cg_rera_extractor/ai/gen/seo.py`

## Tests to Run
- `pytest tests/unit/ai/test_seo.py`

## Acceptance Criteria
- [ ] Templates populated correctly.
- [ ] No truncation of critical keywords.

### Example Test
```bash
python scripts/gen_seo.py --limit 10
```
