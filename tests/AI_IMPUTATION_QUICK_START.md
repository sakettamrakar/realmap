# AI Imputation Feature - Quick Start Guide

## Overview
The AI-powered missing data imputation feature uses machine learning to predict missing `total_units` and `proposed_end_date` values for real estate projects based on their geographic location and developer information.

## Quick Start

### 1. Run Dry Test (No Database Write)
```powershell
$env:PYTHONPATH = "C:\GIT\realmap"
python scripts/run_imputation.py --limit 5 --dry-run
```

### 2. Run Real Imputation
```powershell
$env:PYTHONPATH = "C:\GIT\realmap"
python scripts/run_imputation.py --limit 10
```

### 3. View Results
```python
from cg_rera_extractor.db.models import ProjectImputation
from sqlalchemy import select

# Query all imputations
stmt = select(ProjectImputation).order_by(ProjectImputation.created_at.desc())
imputations = session.scalars(stmt).all()

for imp in imputations:
    print(f"Project {imp.project_id}: {imp.imputed_data}")
```

## How It Works

### Training Phase
1. Loads all projects from database
2. Extracts features: latitude, longitude, project_type, developer_id
3. Extracts targets: total_units, proposed_end_date (year)
4. Trains sklearn IterativeImputer with BayesianRidge estimator
5. Tracks which features have training data available

### Prediction Phase
1. Scans projects for missing values
2. For each incomplete project:
   - Constructs feature vector
   - Runs prediction through trained model
   - Only returns predictions for originally missing fields
   - Saves to `project_imputations` table

## Current Status

### ✅ Working
- **Database:** `project_imputations` table created
- **Dependencies:** scikit-learn installed
- **Tests:** All passing (1/1 unit, 4/4 integration)
- **Predictions:** `proposed_end_date` (9 training samples)

### ⚠️ Limited
- **Predictions:** `total_units` (0 training samples - needs data)
- **Geographic Coverage:** Only 2/10 projects have coordinates

## Example Output

### Dry Run
```
INFO - Step 1: Training Model...
INFO - Loaded 10 rows. Feature columns: ['latitude', 'longitude', 'project_type_encoded', 
                                          'developer_id', 'total_units_impute', 
                                          'possession_year_impute']
INFO - Model trained successfully. Active features: ['latitude', 'longitude', 
                                                      'project_type_encoded', 'developer_id', 
                                                      'possession_year_impute']
INFO - Step 2: Identifying projects with missing data...
INFO - Scanning 5 recent projects check for gaps...
INFO - Project 10: Found gaps. Prediction: {'proposed_end_date': '2022-12-31'}
INFO - Completed. Scanned: 5, Imputed: 1
```

### Database Result
```json
{
  "id": 1,
  "project_id": 10,
  "model_name": "IterativeImputer_v1",
  "confidence_score": 0.850,
  "imputed_data": {
    "proposed_end_date": "2022-12-31"
  },
  "created_at": "2025-12-11 14:18:51.328794+05:30"
}
```

## API Reference

### ImputationEngine

```python
from ai.imputation.engine import ImputationEngine
from sqlalchemy.orm import Session

# Initialize
engine = ImputationEngine(session: Session)

# Train model
engine.train()

# Predict for a project
prediction = engine.predict_project(project_id: int) -> Dict[str, Any]
# Returns: {'total_units': 150, 'proposed_end_date': '2024-12-31'}

# Save prediction
engine.save_imputation(project_id: int, data: Dict[str, Any])
```

### CLI Script

```bash
usage: run_imputation.py [-h] [--limit LIMIT] [--dry-run]

options:
  --limit LIMIT  Process only N most recent projects
  --dry-run      Test mode without saving to database
```

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'ai'"
**Solution:** Set PYTHONPATH
```powershell
$env:PYTHONPATH = "C:\GIT\realmap"
```

### Warning: "Skipping features without any observed values: [4]"
**Meaning:** Feature index 4 (`total_units_impute`) has all NaN values
**Impact:** None - system continues to work, predicting other features
**Solution:** Add projects with total_units data to enable this prediction

### Error: "cannot convert float NaN to integer"
**Solution:** Already fixed in latest code - update `ai/imputation/engine.py`

## Files Modified

- ✅ `ai/imputation/engine.py` - Core imputation logic (223 lines)
- ✅ `scripts/run_imputation.py` - CLI script
- ✅ `cg_rera_extractor/db/models.py` - Added ProjectImputation model
- ✅ `alembic_migrations/versions/d1e2f3a4b5c6_*.py` - Database migration
- ✅ `tests/ai/test_imputation_integration.py` - Unit tests

## Documentation

- **Full Report:** `tests/UAT_AI_IMPUTATION_REPORT.md` (500+ lines)
- **This Guide:** `tests/AI_IMPUTATION_QUICK_START.md`

## Next Steps

1. **Add Training Data:** Import projects with total_units values
2. **Monitor Quality:** Check prediction accuracy against known values
3. **Calculate Confidence:** Replace placeholder 0.85 with real scores
4. **API Endpoint:** Add REST endpoint for on-demand imputation

## Support

For detailed information, see `tests/UAT_AI_IMPUTATION_REPORT.md`
