-- Migration: V002_add_ai_scores
-- Description: Adds ai_scores table and links it to projects

BEGIN;

CREATE TABLE IF NOT EXISTS ai_scores (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    score_value NUMERIC,
    confidence NUMERIC,
    explanation TEXT,
    input_features JSONB,
    provenance JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE projects ADD COLUMN IF NOT EXISTS latest_ai_score_id INTEGER REFERENCES ai_scores(id);

COMMIT;
