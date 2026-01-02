# ETL Diff Report

> **Date**: December 10, 2024  
> **Scope**: Parser, Mapper, and Loader modules

---

## Summary

This document summarizes all ETL code changes made to address data audit findings.

---

## 1. Mapper Module (`cg_rera_extractor/parsing/mapper.py`)

### Changes Made

#### 1.1 New Import: `datetime`
```python
# Before
from typing import Dict, Tuple

# After
from datetime import datetime
from typing import Dict, List, Tuple
```

#### 1.2 New Function: `_normalize_date()`
```python
def _normalize_date(value: str | None) -> str | None:
    """Normalize date strings to ISO format (YYYY-MM-DD).
    
    Handles common Indian date formats:
    - DD/MM/YYYY
    - DD-MM-YYYY
    - DD.MM.YYYY
    - YYYY-MM-DD (already ISO)
    """
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    
    date_formats = (
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%Y/%m/%d",
    )
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return None
```

**Impact**: Fixes 100% NULL rate on `approved_date` and `proposed_end_date` columns.

#### 1.3 New Function: `_extract_pincode()`
```python
def _extract_pincode(address: str | None) -> str | None:
    """Extract 6-digit Indian pincode from address string."""
    if not address:
        return None
    match = re.search(r'\b(\d{6})\b', address)
    return match.group(1) if match else None
```

**Impact**: Populates `pincode` column from address field.

#### 1.4 New Function: `_infer_doc_type()`
```python
def _infer_doc_type(field_key: str) -> str:
    """Infer document type from field key."""
    key_lower = field_key.lower()
    
    doc_type_mapping = {
        'registration': 'registration_certificate',
        'building': 'building_plan',
        'layout': 'layout_plan',
        # ... 14 total mappings
    }
    
    for keyword, doc_type in doc_type_mapping.items():
        if keyword in key_lower:
            return doc_type
    
    return 'unknown'
```

**Impact**: Enables document classification in `project_artifacts`.

#### 1.5 Enhanced Project Details Mapping

```python
# Before
project_details = V1ProjectDetails(
    ...
    launch_date=project_section.get("launch_date"),
    expected_completion_date=project_section.get("expected_completion_date"),
)

# After
project_address = project_section.get("project_address")

# Extract pincode from address if not provided separately
pincode = project_section.get("pincode")
if not pincode and project_address:
    pincode = _extract_pincode(project_address)

# Extract village/locality
village_or_locality = project_section.get("village_or_locality")

# Extract project website
project_website_url = project_section.get("project_website")

project_details = V1ProjectDetails(
    ...
    launch_date=_normalize_date(project_section.get("launch_date")),
    expected_completion_date=_normalize_date(project_section.get("expected_completion_date")),
)

# Store extracted fields for loader to use
project_details._extra = {
    "pincode": pincode,
    "village_or_locality": village_or_locality,
    "project_website_url": project_website_url,
}
```

**Impact**: 
- Dates are now parsed correctly (was 100% NULL)
- Pincode extracted from address
- Village/locality captured
- Project website URL captured

---

## 2. Loader Module (`cg_rera_extractor/db/loader.py`)

### Changes Made

#### 2.1 New Function: `_infer_artifact_category()`
```python
def _infer_artifact_category(field_key: str) -> str:
    """Infer artifact category from field key for document classification.
    
    Categories: 'legal', 'technical', 'approvals', 'media', 'unknown'
    """
    key_lower = field_key.lower()
    
    legal_keywords = ['registration', 'encumbrance', 'title', 'revenue', ...]
    technical_keywords = ['building', 'layout', 'structure', 'floor', ...]
    approval_keywords = ['noc', 'approval', 'permission', 'certificate', ...]
    media_keywords = ['photo', 'image', 'brochure', 'video', ...]
    
    # ... keyword matching logic
    
    return 'unknown'
```

**Impact**: Artifacts now have proper category classification instead of always "unknown".

#### 2.2 Fixed Provenance Record Creation

```python
# Before (caused AttributeError)
source_domain=metadata.source_domain or "rera.cg.gov.in",
parser_version=metadata.scraper_version,

# After (safe with getattr)
source_domain = getattr(metadata, 'source_domain', None) or "rera.cg.gov.in"
scraper_version = getattr(metadata, 'scraper_version', None) or "1.0"

provenance = DataProvenance(
    ...
    source_domain=source_domain,
    extraction_method=f"v1_json_parser_{scraper_version}",
    parser_version=scraper_version,
    ...
)
```

**Impact**: Provenance records now created without `AttributeError`.

#### 2.3 Enhanced Project Loading

```python
# Before
project.village_or_locality = None
project.full_address = details.project_address

# After
extra = getattr(details, '_extra', {}) or {}
pincode = extra.get('pincode')
village_or_locality = extra.get('village_or_locality')
project_website_url = extra.get('project_website_url') or details.project_website_url

project.village_or_locality = village_or_locality
project.pincode = pincode
project.full_address = details.project_address

# Set scraped_at timestamp (AUDIT FIX: was always NULL)
scraped_at_str = v1_project.metadata.scraped_at
if scraped_at_str:
    try:
        project.scraped_at = datetime.fromisoformat(scraped_at_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        project.scraped_at = datetime.now(timezone.utc)
else:
    project.scraped_at = datetime.now(timezone.utc)

# Set project_website_url if schema supports it
if hasattr(project, 'project_website_url'):
    project.project_website_url = project_website_url
```

**Impact**: 
- `scraped_at` now populated (was 100% NULL)
- `village_or_locality` now populated (was 100% NULL)
- `pincode` now populated (was 100% NULL)
- `project_website_url` now populated

#### 2.4 Fixed Land Parcels Loading

```python
# Before
(LandParcel, []),  # Land details not directly in V1Project top-level yet

# After
(LandParcel, v1_project.land_details),  # AUDIT FIX: was hardcoded empty
```

**Impact**: Land parcel data now loaded when available.

#### 2.5 Enhanced Artifact Extraction

```python
# Before
session.add(
    ProjectArtifact(
        project_id=project.id,
        category="unknown",
        artifact_type=field_key,
        file_path=file_path,
        source_url=None,
        is_preview=True,
    )
)

# After
# Get base URL for resolving relative paths
base_url = v1_project.metadata.source_url or ""

# AUDIT FIX: Resolve relative URLs to absolute
if file_path and file_path.startswith(".."):
    from urllib.parse import urljoin
    file_path = urljoin(base_url, file_path)

# AUDIT FIX: Infer category from field key
category = _infer_artifact_category(field_key)

session.add(
    ProjectArtifact(
        project_id=project.id,
        category=category,
        artifact_type=field_key,
        file_path=file_path,
        source_url=file_path,  # Store original URL
        is_preview=True,
    )
)
```

**Impact**: 
- Relative URLs now resolved to absolute paths
- Proper category inference instead of "unknown"
- Source URL stored for reference

---

## 3. Configuration (`logical_sections_and_keys.json`)

### Complete Rewrite

The configuration file was completely rewritten with expanded key variants for all sections.

#### Key Expansion Summary

| Section | Keys Before | Keys After | Variants Before | Variants After |
|---------|-------------|------------|-----------------|----------------|
| project_details | ~12 | 18 | ~25 | ~80 |
| promoter_details | ~6 | 10 | ~15 | ~60 |
| land_details | ~4 | 8 | ~10 | ~40 |
| building_details | ~5 | 10 | ~10 | ~35 |
| unit_types | ~6 | 8 | ~12 | ~30 |
| bank_details | ~4 | 6 | ~8 | ~20 |
| documents | ~4 | 4 | ~8 | ~15 |
| quarterly_updates | ~4 | 10 | ~8 | ~30 |

#### New Keys Added

**project_details**:
- `village_or_locality`: 9 variants (village, locality, mohalla, ward, sector, colony, etc.)
- `project_website`: 6 variants
- `pincode`: 6 variants
- `project_phases`, `fsi_approved`, `far_approved`, `has_litigation`, `open_space_area`, `building_coverage`

**promoter_details**:
- `promoter_phone`: 12 variants (contact number, mobile, mob no, phone no, telephone, etc.)
- `promoter_address`: 7 variants (registered address, office address, correspondence address, etc.)
- `promoter_gst`: 6 variants
- `authorized_signatory`: 4 variants

**building_details**:
- Section title variants expanded to 9 (tower details, block details, wing details, etc.)
- Added `basement_floors`, `stilt_floors`, `podium_floors`, `building_height`, `parking_slots`

**quarterly_updates**:
- Added `foundation_percent`, `plinth_percent`, `superstructure_percent`, `mep_percent`, `finishing_percent`

---

## 4. New Utility Module (`cg_rera_extractor/utils/normalize.py`)

### Module Overview

| Category | Functions | Lines |
|----------|-----------|-------|
| Area Conversion | 4 | ~100 |
| Price Normalization | 3 | ~70 |
| Category Normalization | 2 | ~50 |
| Text Normalization | 4 | ~40 |
| Constants | 8 | ~20 |
| **Total** | **21** | **~335** |

### Key Features

1. **Area Conversion**
   - Handles sqft, sqm, sqyd, acres, hectares, bigha
   - Auto-detects unit from string (e.g., "1000 sq.ft")
   - Handles Indian number formatting (commas)

2. **Price Normalization**
   - Handles ₹ symbol, Rs. prefix
   - Converts lakhs (L, Lac, Lakh) to numeric
   - Converts crores (Cr, Crore) to numeric
   - Handles mixed formats ("₹1.5 Cr", "50 L")

3. **Category Normalization**
   - Standard project status values (ongoing, completed, approved, expired)
   - Standard project type values (residential, commercial, mixed, plotted)

---

## 5. Impact Summary

### Fields Now Populated (Previously 100% NULL)

| Field | Root Cause | Fix Applied |
|-------|------------|-------------|
| `projects.scraped_at` | Not set in loader | Set from metadata or current time |
| `projects.approved_date` | Date parsing broken | Added `_normalize_date()` |
| `projects.proposed_end_date` | Date parsing broken | Added `_normalize_date()` |
| `projects.village_or_locality` | Not extracted | Added key variants + loader mapping |
| `projects.pincode` | Not extracted | Added `_extract_pincode()` |
| `promoters.phone` | Key mismatch | Added 12 key variants |
| `promoters.address` | Key mismatch | Added 7 key variants |
| `promoters.promoter_type` | Key mismatch | Added 8 key variants |

### Tables Now Populated (Previously Empty)

| Table | Fix Applied |
|-------|-------------|
| `land_parcels` | Changed from hardcoded `[]` to `v1_project.land_details` |
| `data_provenance` | Fixed AttributeError in creation |

### Data Quality Improvements

| Metric | Before | After (Expected) |
|--------|--------|------------------|
| Date fields populated | 0% | 80%+ |
| Pincode populated | 0% | 60%+ |
| Village/locality populated | 0% | 70%+ |
| Artifact categories classified | 0% | 90%+ |
| Provenance records created | 0% | 100% |

---

## 6. Test Coverage

| Module | Test File | Tests |
|--------|-----------|-------|
| `mapper._normalize_date` | `tests/test_mapper.py` | 10 |
| `mapper._extract_pincode` | `tests/test_mapper.py` | 8 |
| `mapper._infer_doc_type` | `tests/test_mapper.py` | 11 |
| `normalize.normalize_area_*` | `tests/test_normalize.py` | 9 |
| `normalize.normalize_price` | `tests/test_normalize.py` | 14 |
| `normalize.normalize_project_*` | `tests/test_normalize.py` | 7 |
| `normalize.*_text` | `tests/test_normalize.py` | 5 |
| **Total** | | **64** |

All 64 tests passing ✅
