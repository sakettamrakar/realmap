# Release Notes: v1-ai-score

**Version**: 1.0.0
**Date**: 2025-12-10

## Summary
Introduces the AI-powered Project Quality Score, providing automated 0-100 scoring based on location, amenities, and compliance data.

## Features
- **Project Quality Score**: Holistic score derived from `amenity`, `location`, and `compliance` signals.
- **Explainability**: LLM-generated rationale for each score.
- **Microservice**: New `/ai` endpoints for scoring.

## API Documentation
### GET /ai/score/project/{id}
Returns calculation for a given project.
```json
{
  "score_value": 85.5,
  "confidence": 0.9,
  "explanation": "..."
}
```

## Data Model Changes
- **New Table**: `ai_scores` maps scorings to projects and model versions.
  - Columns: `project_id`, `score`, `confidence`, `explanation`, `model_name`, `input_features`.

## Configuration
- **Feature Flag**: `AI_ENABLED` (must be set to `true` in `config.yaml`).
- **Disabling**: Set `AI_ENABLED=false` to revert to legacy scoring or hide scores.

## Monitoring & Runbooks
- **Metrics**: `ai_latency`, `ai_error_rate`, `ai_fallback_rate`.
- **Alerts**: Triggered if Error Rate > 5% or Latency p95 > 2s.
- **Rollback**:
  1. Set `AI_ENABLED=false`.
  2. Redeploy `main` branch.
