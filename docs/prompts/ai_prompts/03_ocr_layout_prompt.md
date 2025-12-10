# 03 OCR Layout Prompt

## Role
Computer Vision Engineer.

## Goal
Implement **AI-powered OCR and Layout Parsing** for Floor Plans. Detect room labels ("Kitchen", "Master Bed") and dimensions within images.

## Inputs
- **Files:** Images in `/data/images/floor_plans/`.
- **Model:** `Surya-OCR` or `PaddleOCR` (lightweight) or Vision LLM.

## Outputs
- **Code:** `cg_rera_extractor/ai/vision/floor_plan_analyzer.py`
- **Database:** Update `project_media` table with `meta_tags` JSONB column.

## Constraints
- **Format:** Output must be GeoJSON-like or simple JSON list of regions.
- **Speed:** < 5s per image.

## Files to Modify
- `cg_rera_extractor/ai/vision/floor_plan_analyzer.py`

## Tests to Run
- `pytest tests/unit/ai/test_vision.py`

## Acceptance Criteria
- [ ] Script reads an image `1bhk.jpg`.
- [ ] Returns list of rooms: `[{ "label": "Kitchen", "dims": "10x8" }]`.
- [ ] Data stored in `project_media.meta_tags`.

### Example Test (Curl)
```bash
curl -X POST "http://localhost:8001/api/v1/vision/analyze_plan" \
  -F "file=@1bhk.jpg"
# Returns: { "rooms": [...] }
```
