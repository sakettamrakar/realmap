# 08 Auto Description Prompt

## Role
Generative AI Engineer.

## Goal
Implement **Auto-generated Project Descriptions**. Create engaging marketing copy from structured attributes.

## Inputs
- **Data:** Project Attributes (Name, BHK, Amenities, Locality).
- **Model:** Qwen2.5-7B-Instruct.

## Outputs
- **Code:** `cg_rera_extractor/ai/gen/description.py`
- **Database:** `projects.ai_description` column.

## Constraints
- **Tone:** Professional, inviting, SEO-friendly.
- **Factuality:** No hallucinations (do not invent amenities).

## Files to Modify
- `cg_rera_extractor/ai/gen/description.py`

## Tests to Run
- `pytest tests/unit/ai/test_gen.py`

## Acceptance Criteria
- [ ] Valid text generated (~150 words).
- [ ] Includes keywords (Location, Project Name).
- [ ] Saved to DB.

### Example Test
```bash
python scripts/gen_desc.py --project_id 1
```
