# RERA Document Interpretation - UAT Guide

## Quick Start

```powershell
# Run comprehensive UAT
python tests/uat_rera_document_interpretation.py
```

## Test Coverage

### ✅ Test 1: Database Schema Verification
- Verifies `rera_filings` table exists
- Checks all required columns
- Validates indexes

### ✅ Test 2: Test Project Creation
- Creates UAT test project
- Ensures clean test environment

### ✅ Test 3: Valid PDF Processing (CLI)
- Tests PDF text extraction
- Verifies database insertion
- Checks status tracking

### ✅ Test 4: Invalid PDF Handling
- Tests error graceful handling
- Verifies error messages stored
- Checks error status set correctly

### ✅ Test 5: Batch Processing
- Processes multiple PDFs
- Verifies all PDFs handled
- Tests performance

### ✅ Test 6: API Endpoint Verification
- Tests POST `/ai/extract/rera`
- Requires AI service running
- Validates HTTP responses

### ✅ Test 7: Database Queries
- Tests data retrieval
- Verifies query performance
- Checks filtering capabilities

### ✅ Test 8: Error Recovery
- Tests non-existent file handling
- Verifies error logging
- Checks system resilience

### ✅ Test 9: Data Integrity
- Checks for orphaned records
- Verifies required fields
- Validates referential integrity

## Prerequisites

```powershell
# Install required packages
pip install reportlab  # For test PDF generation
pip install requests   # For API testing

# Ensure database is running
# Ensure migrations are applied: alembic upgrade head
```

## API Service (Optional for Test 6)

```powershell
# Terminal 1: Start AI service
uvicorn ai.main:app --reload --port 8000

# Terminal 2: Run UAT
python tests/uat_rera_document_interpretation.py
```

## Expected Output

```
==================================================================
  RERA DOCUMENT INTERPRETATION - USER ACCEPTANCE TESTING
==================================================================

==================================================================
  Test 1: Database Schema Verification
==================================================================

✓ rera_filings table exists
✓ All required columns present (9 total)
  Columns: id, project_id, file_path, doc_type, raw_text, extracted_data, status, error_message, created_at

...

==================================================================
  UAT TEST SUMMARY
==================================================================

Total Tests: 20
Passed: 18
Failed: 0
Warnings: 2

✓ PASSED TESTS:
  ✓ Database schema: rera_filings table
  ✓ Database schema: All columns present
  ✓ Test project creation: ID 123
  ...

======================================================================
✓ UAT PASSED - Feature is ready for production
======================================================================
```

## Troubleshooting

### Database Connection Issues
```powershell
# Check DATABASE_URL environment variable
echo $env:DATABASE_URL

# Or update config.yaml with correct credentials
```

### PDF Generation Issues
```powershell
# Install reportlab if missing
pip install reportlab
```

### API Service Not Running
- Test 6 will show warning if API service is not running
- This is non-critical; other tests will still pass
- Start service with: `uvicorn ai.main:app --reload`

## Cleanup

```powershell
# Remove UAT test project (optional)
python -c "from sqlalchemy import create_engine, text; from cg_rera_extractor.config.loader import load_config; config = load_config('config.yaml'); engine = create_engine(config.db.url); engine.execute(text('DELETE FROM rera_filings WHERE project_id IN (SELECT id FROM projects WHERE rera_registration_no = \\'UAT_TEST_PROJECT_001\\')'));"
```

## Integration with CI/CD

```yaml
# Add to .github/workflows/test.yml
- name: Run RERA UAT
  run: python tests/uat_rera_document_interpretation.py
```

## Success Criteria

- ✅ All 9 test categories pass
- ✅ No failed tests
- ✅ Warnings (if any) are documented and acceptable
- ✅ Database integrity maintained
- ✅ Error handling works gracefully
