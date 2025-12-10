# Automated Verification Report

**Generated:** December 10, 2025  
**Report Version:** 1.0  
**Project:** RealMap AI Microservice

---

## Executive Summary

| Category | Status | Details |
|----------|--------|---------|
| Unit Tests | ✅ **PASS** | 2/2 tests passed |
| Integration Tests | ❌ **FAIL** | 0 tests run (import error) |
| Linter (Ruff) | ⚠️ **WARNINGS** | 132 errors found (73 auto-fixable) |
| Type Checking (MyPy) | ⚠️ **WARNINGS** | 171 type errors found |
| OpenAPI Contract | ❌ **BLOCKED** | Cannot validate (FastAPI dependency issue) |
| DB Migrations | ✅ **VERIFIED** | `ai_scores` table migration exists |

**Overall Status:** ⚠️ **REQUIRES ACTION** - Critical dependency issue blocking integration tests and API validation.

---

## 1. Unit Tests Results

### Summary
- **Total Tests:** 2
- **Passed:** 2 ✅
- **Failed:** 0
- **Skipped:** 0
- **Duration:** 1.68s

### Test Details
```
tests/test_ai_unit.py::test_feature_builder_structure PASSED [ 50%]
tests/test_ai_unit.py::test_scoring_logic PASSED            [100%]
```

### Code Coverage (Unit Tests)
- **Overall Coverage:** 44% (84/189 statements)
- **Target:** 80%+ ⚠️ **Below Target**

| Module | Statements | Covered | Missing | Coverage |
|--------|------------|---------|---------|----------|
| `ai/schemas.py` | 25 | 25 | 0 | 100% ✅ |
| `ai/features/builder.py` | 30 | 26 | 4 | 87% ✅ |
| `ai/scoring/logic.py` | 24 | 17 | 7 | 71% ⚠️ |
| `ai/llm/adapter.py` | 61 | 16 | 45 | 26% ❌ |
| `ai/main.py` | 49 | 0 | 49 | 0% ❌ |

**Critical Gaps:**
- `ai/main.py` has 0% coverage - FastAPI endpoints not tested
- `ai/llm/adapter.py` has 26% coverage - LLM integration not tested
- `ai/scoring/logic.py` missing coverage for LLM-based scoring paths

---

## 2. Integration Tests Results

### Summary
- **Status:** ❌ **CRITICAL FAILURE**
- **Total Tests:** 0 (failed to collect)
- **Root Cause:** FastAPI dependency injection error

### Error Details
```python
fastapi.exceptions.FastAPIError: Invalid args for response field! 
Hint: check that <class 'sqlalchemy.engine.base.Engine'> is a valid Pydantic field type.
```

**Location:** `ai/main.py:31` - `@app.post("/ai/score/project/{project_id}")`

**Root Cause Analysis:**
The `get_session_local` function from `cg_rera_extractor.db` is being used incorrectly as a FastAPI dependency. This function requires an `engine` parameter and returns a `sessionmaker`, not a `Session` instance.

**Current Code (Incorrect):**
```python
from cg_rera_extractor.db import get_session_local

@app.post("/ai/score/project/{project_id}")
async def score_project(project_id: int, db: Session = Depends(get_session_local)):
    ...
```

**Issue:** `get_session_local(engine)` returns a sessionmaker factory, not a callable dependency.

---

## 3. Linter Results (Ruff)

### Summary
- **Total Errors:** 132
- **Auto-fixable:** 73
- **Manual fixes required:** 59

### Error Breakdown by Category

| Category | Count | Severity |
|----------|-------|----------|
| F401 - Unused imports | 45 | Low |
| E712 - `== True` comparisons | 6 | Medium |
| E402 - Import not at top of file | 16 | Medium |
| F541 - f-string without placeholders | 7 | Low |
| E722 - Bare `except` clause | 3 | High ⚠️ |
| F811 - Redefinition | 1 | High ⚠️ |
| F841 - Unused variable | 3 | Low |
| E701 - Multiple statements on one line | 2 | Low |
| Others | 49 | Mixed |

### Top Priority Issues

1. **High Priority - Bare except clauses (E722):**
   - `debug_rera_selectors.py:53`
   - `debug_status_options.py:53`
   - `scripts/ux_smoke_test.py:24`
   
   **Risk:** Catches all exceptions including system exits and keyboard interrupts.

2. **High Priority - Redefined import (F811):**
   - `cg_rera_extractor/db/__init__.py:12` - `AmenityPOI` imported twice
   
   **Risk:** Can cause import confusion and bugs.

3. **Medium Priority - Boolean comparisons (E712):**
   - Multiple files using `== True` instead of direct boolean checks
   - Examples: `api/services/discovery.py:426`, `api/services/search.py:283`
   
   **Impact:** Code style and potential subtle bugs.

### Auto-Fix Recommendation
```bash
ruff check . --fix
```
This will automatically fix 73 of the 132 issues (55%).

---

## 4. Type Checking Results (MyPy)

### Summary
- **Total Errors:** 171
- **Files Checked:** 99
- **Files with Errors:** 31

### Error Categories

| Error Type | Count | Description |
|------------|-------|-------------|
| Numeric conversion issues | 87 | `Numeric[Any]` to `float` conversions |
| Missing named arguments | 18 | Pydantic model initialization issues |
| Union attribute access | 15 | Accessing attributes on Union types |
| Incompatible types | 24 | Type mismatches in assignments |
| Import issues | 4 | Missing type stubs for `requests`, `yaml` |
| Others | 23 | Mixed type issues |

### Critical Type Errors

1. **AI Module - Dependency Issue:**
   ```
   ai/features/builder.py:13: Missing positional argument "engine" in call to "get_session_local"
   ai/features/builder.py:13: Incompatible types (expression has type "sessionmaker[Session]", variable has type "Session")
   ```
   **Impact:** Same root cause as integration test failure.

2. **Numeric Conversion Pattern (87 occurrences):**
   ```
   Argument 1 to "float" has incompatible type "Numeric[Any]"
   ```
   **Location:** Throughout API services, amenities, geo modules
   **Impact:** SQLAlchemy `Numeric` type not being properly cast.

3. **Missing Pydantic Arguments (18 occurrences):**
   ```
   Missing named argument "@type" for "SchemaOrgProduct"
   Missing named argument "official_link" for "TrustBadge"
   ```
   **Location:** `api/services/jsonld.py`, `api/services/analytics.py`
   **Impact:** Schema.org and API response models incomplete.

### Recommended Fixes

**For Numeric conversions:** Add explicit type casts or use SQLAlchemy `cast()`:
```python
# Before
price = project.price_min_sqft
score = float(project.overall_score)

# After
from sqlalchemy import cast, Float
price = float(project.price_min_sqft) if project.price_min_sqft else None
score = float(cast(project.overall_score, Float)) if project.overall_score else 0.0
```

**For missing type stubs:**
```bash
pip install types-PyYAML types-requests
```

---

## 5. OpenAPI Contract Validation

### Status
❌ **BLOCKED** - Cannot generate OpenAPI schema due to FastAPI dependency error.

### Impact
- API documentation generation fails
- `/ai/docs` endpoint non-functional
- `/ai/openapi.json` cannot be generated
- Contract testing blocked

### Required Before Validation
Fix the FastAPI dependency injection issue in `ai/main.py` (see Integration Tests section).

---

## 6. Database Migration Verification

### Summary
✅ **VERIFIED** - `ai_scores` table migration exists and is properly defined.

### Migration Details
- **File:** `migrations/V002_add_ai_scores.sql`
- **Status:** Migration script exists
- **Table:** `ai_scores`
- **Foreign Key:** `projects.latest_ai_score_id` → `ai_scores.id`

### Schema Verification
```sql
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

ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS latest_ai_score_id INTEGER REFERENCES ai_scores(id);
```

### Migration Status Check
⚠️ **Note:** Migration script exists but actual database application status not verified.

**Recommendation:** Run migration status check:
```bash
python migrations/run_migration.py --status
```

---

## 7. Critical Issues & Fixes

### 🔴 **BLOCKER #1: FastAPI Dependency Injection Error**

**Priority:** P0 - Blocks all integration tests and API functionality  
**File:** `ai/main.py`  
**Lines:** 31, 103

**Problem:**
```python
# Current (incorrect):
from cg_rera_extractor.db import get_session_local

@app.post("/ai/score/project/{project_id}")
async def score_project(project_id: int, db: Session = Depends(get_session_local)):
    ...
```

**Solution:**
Create a proper FastAPI dependency function:

```python
# ai/main.py
from cg_rera_extractor.db import get_engine, get_session_local
from sqlalchemy.orm import Session
from typing import Generator

# Create engine at module level
_engine = get_engine()
_SessionLocal = get_session_local(_engine)

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Use the dependency:
@app.post("/ai/score/project/{project_id}")
async def score_project(project_id: int, db: Session = Depends(get_db)):
    ...
```

**Verification:**
After fix, run:
```bash
pytest tests/test_ai_integration.py -v
```

---

### 🟡 **Issue #2: Low Test Coverage (44%)**

**Priority:** P1 - Quality gate not met  
**Target:** 80%+ coverage  
**Gap:** 36 percentage points

**Missing Coverage Areas:**
1. **FastAPI endpoints** (`ai/main.py`) - 0% coverage
2. **LLM adapter** (`ai/llm/adapter.py`) - 26% coverage
3. **Error handling paths** across all modules

**Action Plan:**
1. Add integration tests for all API endpoints
2. Add unit tests for LLM adapter with mocked `llama-cpp-python`
3. Add error case tests for scoring logic
4. Add tests for edge cases (null values, invalid data)

**Estimated Impact:** +30-35% coverage with 15-20 additional test cases.

---

### 🟡 **Issue #3: Code Quality - 132 Linter Errors**

**Priority:** P2 - Technical debt  
**Auto-fixable:** 73 errors (55%)

**Quick Win Actions:**
```bash
# Auto-fix unused imports, f-string issues, etc.
ruff check . --fix

# Review and manually fix:
# - Bare except clauses (3)
# - Redefined imports (1)
# - Boolean comparison style (6)
```

**Estimated Time:** 1-2 hours for all fixes.

---

### 🟡 **Issue #4: Type Safety - 171 MyPy Errors**

**Priority:** P2 - Type safety and maintainability

**Primary Categories:**
1. **SQLAlchemy Numeric type issues (87)** - Systematic pattern
2. **Pydantic model issues (18)** - Missing required fields
3. **Union type handling (15)** - Needs narrowing

**Action Plan:**
1. Install missing type stubs: `pip install types-PyYAML types-requests`
2. Create utility functions for common type conversions
3. Fix Pydantic models to include all required fields
4. Add type: ignore comments for known SQLAlchemy issues (temporary)

**Estimated Time:** 4-6 hours with pattern-based fixes.

---

## 8. Next Steps & Recommendations

### Immediate Actions (This Sprint)

1. **🔴 P0 - Fix FastAPI Dependency (Blocker)**
   - [ ] Create `get_db()` dependency function in `ai/main.py`
   - [ ] Update all endpoint functions to use new dependency
   - [ ] Verify integration tests pass
   - [ ] **Owner:** Backend Lead
   - [ ] **ETA:** 1 hour

2. **🟡 P1 - Increase Test Coverage**
   - [ ] Add integration tests for `/ai/score/project/{id}` endpoint
   - [ ] Add integration test for `/ai/score/{score_id}` endpoint
   - [ ] Add unit tests for error cases in scoring logic
   - [ ] Add mocked LLM adapter tests
   - [ ] **Owner:** QA + Backend
   - [ ] **ETA:** 4-6 hours

3. **🟡 P2 - Code Quality Fixes**
   - [ ] Run `ruff check . --fix` to auto-fix 73 errors
   - [ ] Manually fix 3 bare except clauses
   - [ ] Fix duplicate `AmenityPOI` import
   - [ ] Fix boolean comparison style (6 occurrences)
   - [ ] **Owner:** Backend Team
   - [ ] **ETA:** 2 hours

### Short-term Actions (Next Sprint)

4. **Type Safety Improvements**
   - [ ] Install type stubs: `pip install types-PyYAML types-requests`
   - [ ] Create utility functions for SQLAlchemy Numeric → float conversions
   - [ ] Fix Pydantic model missing fields (18 occurrences)
   - [ ] Add type narrowing for Union types
   - [ ] **Owner:** Backend Lead
   - [ ] **ETA:** 6-8 hours

5. **API Contract Validation**
   - [ ] After FastAPI fix, generate and save OpenAPI schema
   - [ ] Create contract tests using saved schema
   - [ ] Add to CI/CD pipeline
   - [ ] **Owner:** Backend + DevOps
   - [ ] **ETA:** 3-4 hours

6. **Database Migration Verification**
   - [ ] Run migration status check on dev database
   - [ ] Document migration application procedure
   - [ ] Verify `ai_scores` table exists with correct schema
   - [ ] **Owner:** Database Admin
   - [ ] **ETA:** 1 hour

### Quality Gates for Merge/Deploy

- [ ] All unit tests pass (currently: ✅ 2/2)
- [ ] All integration tests pass (currently: ❌ 0/0 - blocked)
- [ ] Test coverage ≥ 70% (currently: ❌ 44%)
- [ ] Linter errors ≤ 20 (currently: ❌ 132)
- [ ] Type errors ≤ 50 (currently: ❌ 171)
- [ ] OpenAPI schema validates (currently: ❌ blocked)
- [ ] DB migrations applied and verified (currently: ⚠️ script exists)

**Current Status:** 1/7 gates passed ❌

---

## 9. Test Execution Commands

### Run All Tests
```bash
# Unit tests with coverage
pytest tests/test_ai_unit.py -v --cov=ai --cov-report=term --cov-report=html

# Integration tests (after fixing dependency issue)
pytest tests/test_ai_integration.py -v --cov=ai --cov-append

# All tests
pytest tests/ -v --cov=ai --cov-report=term --cov-report=html
```

### Code Quality Checks
```bash
# Linting with auto-fix
ruff check . --fix

# Type checking
mypy ai/ cg_rera_extractor/ --ignore-missing-imports

# All quality checks
ruff check . && mypy ai/ cg_rera_extractor/ --ignore-missing-imports
```

### Database Migration
```bash
# Check migration status
python migrations/run_migration.py --status

# Apply migrations
python migrations/run_migration.py
```

### API Validation (after fix)
```bash
# Generate OpenAPI schema
python -c "from ai.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > reports/openapi_schema.json

# Start API server for manual testing
uvicorn ai.main:app --reload --port 8001
```

---

## 10. CI/CD Integration Recommendations

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ruff
        name: ruff
        entry: ruff check --fix
        language: system
        types: [python]
      
      - id: mypy
        name: mypy
        entry: mypy
        language: system
        types: [python]
        args: [--ignore-missing-imports]
```

### GitHub Actions Workflow
```yaml
name: Verification Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov ruff mypy
      
      - name: Run linter
        run: ruff check . --output-format=github
        continue-on-error: true
      
      - name: Run type checker
        run: mypy ai/ --ignore-missing-imports
        continue-on-error: true
      
      - name: Run tests
        run: pytest tests/ -v --cov=ai --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 11. Appendix

### A. Full Test Output
See: `reports/ruff_output.txt`  
See: `reports/mypy_output.txt`  
See: `reports/coverage_unit.json`

### B. Environment Information
- Python Version: 3.11.9
- FastAPI: Latest
- SQLAlchemy: 2.0+
- Pytest: 8.4.1
- Ruff: 0.14.8
- MyPy: 1.19.0

### C. Related Documentation
- [AI Implementation Guide](../docs/AI_Implementation_Guide.md)
- [API Reference](../docs/API-Reference.md)
- [Database Guide](../docs/DB_GUIDE.md)
- [Development Guide](../docs/DEV_GUIDE.md)

---

**Report Generated by:** QA Agent  
**Verification Suite Version:** 1.0  
**Last Updated:** December 10, 2025 20:45 UTC
