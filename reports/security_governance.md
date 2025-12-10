# Security & Governance Report

**Date**: 2025-12-10
**Agent**: Governance Agent

## Findings

### 1. Secrets Scan
- **Status**: ✅ Passed (Preliminary)
- **Details**: No obvious secrets (`password`, `key`) found in codebase (excluding node_modules).
- **Recommendation**: Integrate specialized secret scanner (e.g., `gitleaks`) in CI/CD.

### 2. PII & Sensitive Data (`ai_scores`)
- **Status**: ⚠️ Warning
- **Details**: 
    - `ai_scores` table exists in database but **NO ORM model definition found** in `cg_rera_extractor/db/models.py`.
    - Cannot verify `input_features` column for PII redaction rules structurally.
    - Table is currently empty.
- **Action Required**: Define `AIScore` model in ORM and ensure `input_features` is marked for PII review.

### 3. Model Provenance
- **Status**: ❓ Unknown
- **Details**: Since `ai_scores` model is missing in code, verified columns via DB inspection only (Count: 0).
- **Requirement**: Ensure `model_name` and `model_version` columns exist.

### 4. Feature Flags
- **Status**: ❌ Failed
- **Details**: `AI_ENABLED` flag NOT found in `config/` files.
- **Action Required**: Add explicit `AI_ENABLED` toggle to `agent-manager.json` or `config.yaml`.

## Remediation Plan
1.  Add `class AIScore(Base): ... __tablename__ = 'ai_scores'` to `models.py`.
2.  Add `AI_ENABLED: boolean` to config schema.
3.  Implement PII scrubber for `input_features` before saving.
