# ETL Fixes Report

> **Audit Date**: December 10, 2024  
> **Scope**: All extraction, parsing, and loading code

---

## Overview

This document identifies specific code areas requiring updates to improve data extraction and storage. Each entry includes the file path, line numbers, issue description, and suggested fix.

---

## 1. Raw Extractor Issues

### File: `cg_rera_extractor/parsing/raw_extractor.py`

#### Issue 1.1: Missing Village/Locality Extraction
- **Lines**: N/A (feature gap)
- **Problem**: `village_or_locality` not captured from page
- **Root Cause**: No selector variant for locality field
- **Fix**:
```python
# In logical_sections_and_keys.json, add to project_details.keys:
"village_or_locality": ["village", "locality", "mohalla", "ward", "sector"]
```

#### Issue 1.2: Pincode Not Parsed from Address
- **Lines**: 89-120 (`_extract_value_and_links`)
- **Problem**: Pincode embedded in address string not extracted
- **Fix**:
```python
# Add regex extraction in mapper.py
import re

def _extract_pincode(address: str | None) -> str | None:
    if not address:
        return None
    match = re.search(r'\b(\d{6})\b', address)
    return match.group(1) if match else None
```

#### Issue 1.3: Preview Hints Have Relative Paths
- **Lines**: 205-233 (`_find_preview_hint`)
- **Problem**: Returns relative paths like `../Content/ProjectDocuments/...`
- **Fix**:
```python
# Normalize preview URLs to absolute paths
def _normalize_preview_url(hint: str, base_url: str) -> str:
    if hint.startswith("../") or hint.startswith("./"):
        from urllib.parse import urljoin
        return urljoin(base_url, hint)
    return hint
```

---

## 2. Mapper Issues

### File: `cg_rera_extractor/parsing/mapper.py`

#### Issue 2.1: Date Parsing Not Working
- **Lines**: 201-202 (project_details mapping)
- **Problem**: `launch_date` and `expected_completion_date` always NULL
- **Root Cause**: Date format mismatch in source data
- **Fix**:
```python
# Before line 201, add date normalization
def _normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    # Try multiple formats
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            dt = datetime.strptime(value.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return value  # Return as-is if parsing fails

# Then use in mapping:
launch_date=_normalize_date(project_section.get("launch_date")),
expected_completion_date=_normalize_date(project_section.get("expected_completion_date")),
```

#### Issue 2.2: Promoter Fields Not Mapping
- **Lines**: 205-218 (promoter_details mapping)
- **Problem**: `promoter_type`, `phone`, `address` all NULL
- **Root Cause**: Key variants don't match HTML labels
- **Fix**: Update `logical_sections_and_keys.json`:
```json
{
  "promoter_phone": ["promoter phone", "contact number", "mobile", "mob no", "phone no", "telephone"],
  "promoter_address": ["promoter address", "address", "registered address", "office address", "correspondence address"],
  "promoter_type": ["promoter type", "application type", "organisation type", "org type", "type of entity"]
}
```

#### Issue 2.3: Building Details Often Empty
- **Lines**: 232-242 (building_details mapping)
- **Problem**: Building details array usually empty
- **Root Cause**: Section title variants don't match
- **Fix**: Update `logical_sections_and_keys.json`:
```json
{
  "logical_section": "building_details",
  "section_title_variants": [
    "building details",
    "tower details",
    "block details",
    "wing details",
    "building information",
    "details of building",
    "tower/building"
  ]
}
```

#### Issue 2.4: Quarterly Updates Not Parsed
- **Lines**: 280-291 (quarterly_updates mapping)
- **Problem**: Updates array always empty
- **Root Cause**: Progress table has different structure
- **Fix**:
```python
# Quarterly updates are often in a table format, not label/value
# Need special table parser in raw_extractor.py

def _extract_progress_table(soup: BeautifulSoup) -> list[dict]:
    """Extract quarterly progress from HTML table."""
    updates = []
    progress_table = soup.find("table", class_=re.compile(r"progress|quarterly", re.I))
    if not progress_table:
        return updates
    
    rows = progress_table.find_all("tr")[1:]  # Skip header
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 3:
            updates.append({
                "quarter": cells[0].get_text(strip=True),
                "status": cells[1].get_text(strip=True),
                "percent": cells[2].get_text(strip=True),
            })
    return updates
```

#### Issue 2.5: Documents Array Empty Despite Data
- **Lines**: 268-278 (documents mapping)
- **Problem**: Document list empty even when documents exist
- **Root Cause**: Documents stored in `previews` dict instead
- **Fix**:
```python
# After line 307, add document extraction from previews
for field_key, preview in previews.items():
    if any(doc_type in field_key.lower() for doc_type in 
           ['certificate', 'plan', 'noc', 'approval', 'document']):
        documents.append(
            V1Document(
                name=field_key,
                document_type=_infer_doc_type(field_key),
                url=preview.notes if preview.notes else None,
                uploaded_on=None,
            )
        )
```

---

## 3. Loader Issues

### File: `cg_rera_extractor/db/loader.py`

#### Issue 3.1: scraped_at Not Set
- **Lines**: 261-270 (project field assignment)
- **Problem**: `project.scraped_at` always NULL
- **Fix**:
```python
# Add at line 270:
project.scraped_at = (
    datetime.fromisoformat(v1_project.metadata.scraped_at.replace('Z', '+00:00'))
    if v1_project.metadata.scraped_at else datetime.now(timezone.utc)
)
```

#### Issue 3.2: Provenance Record Creation Fails Silently
- **Lines**: 161-208 (`_create_provenance_record`)
- **Problem**: Function references non-existent `metadata.source_domain` and `metadata.scraper_version`
- **Fix**:
```python
# Line 195: Use getattr with defaults
source_domain=getattr(metadata, 'source_domain', 'rera.cg.gov.in'),
extraction_method=f"v1_json_parser_{getattr(metadata, 'scraper_version', '1.0')}",
parser_version=getattr(metadata, 'scraper_version', '1.0'),
```

#### Issue 3.3: Buildings Array Not Loaded
- **Lines**: 336-348 (buildings loading)
- **Problem**: `v1_project.building_details` always empty
- **Root Cause**: Upstream mapper issue (see 2.3)
- **Fix**: After fixing mapper, also add fallback:
```python
# Try to extract buildings from raw_data if main list empty
if not v1_project.building_details and v1_project.raw_data:
    building_section = v1_project.raw_data.sections.get("building_details", {})
    if building_section:
        # Parse single building from section data
        buildings = [V1BuildingDetails(**building_section)]
```

#### Issue 3.4: Land Parcels Never Populated
- **Lines**: 312 (LandParcel loading)
- **Problem**: Empty list hardcoded
- **Fix**:
```python
# Replace line 312:
(LandParcel, v1_project.land_details),  # Was []
```

#### Issue 3.5: Artifacts from Previews Incomplete
- **Lines**: 411-436 (artifacts loading)
- **Problem**: `file_path` stored in notes but URL not resolved
- **Fix**:
```python
# Improve artifact extraction at line 424
base_url = v1_project.metadata.source_url or ""
file_path = notes if notes and isinstance(notes, str) else None

# Resolve relative URLs
if file_path and file_path.startswith(".."):
    from urllib.parse import urljoin
    file_path = urljoin(base_url, file_path)

session.add(
    ProjectArtifact(
        project_id=project.id,
        category=_infer_artifact_category(field_key),
        artifact_type=field_key,
        file_path=file_path,
        source_url=file_path,  # Store original URL
        is_preview=True,
    )
)
```

---

## 4. Price Computation Issues

### File: `cg_rera_extractor/db/loader.py` (New Addition Needed)

#### Issue 4.1: Price-per-sqft by Area Type Not Computed
- **Lines**: N/A (feature gap)
- **Problem**: `price_per_sqft_carpet_*` and `price_per_sqft_sbua_*` always NULL
- **Fix**:
```python
# Add after line 464, before returning stats

def _compute_price_per_sqft(session: Session, project_id: int):
    """Compute and store price per sqft by area type."""
    from sqlalchemy import select
    from cg_rera_extractor.db import ProjectUnitType, ProjectPricingSnapshot
    
    unit_types = session.execute(
        select(ProjectUnitType).where(ProjectUnitType.project_id == project_id)
    ).scalars().all()
    
    for ut in unit_types:
        snapshot = session.execute(
            select(ProjectPricingSnapshot).where(
                ProjectPricingSnapshot.project_id == project_id,
                ProjectPricingSnapshot.unit_type_label == ut.unit_label
            )
        ).scalar_one_or_none()
        
        if not snapshot:
            continue
        
        # Calculate carpet area price
        if ut.carpet_area_min_sqft and snapshot.min_price_total:
            snapshot.price_per_sqft_carpet_min = (
                snapshot.min_price_total / ut.carpet_area_min_sqft
            )
        if ut.carpet_area_max_sqft and snapshot.max_price_total:
            snapshot.price_per_sqft_carpet_max = (
                snapshot.max_price_total / ut.carpet_area_max_sqft
            )
        
        # Calculate SBUA price
        if ut.super_builtup_area_min_sqft and snapshot.min_price_total:
            snapshot.price_per_sqft_sbua_min = (
                snapshot.min_price_total / ut.super_builtup_area_min_sqft
            )
        if ut.super_builtup_area_max_sqft and snapshot.max_price_total:
            snapshot.price_per_sqft_sbua_max = (
                snapshot.max_price_total / ut.super_builtup_area_max_sqft
            )
```

---

## 5. Configuration Updates Required

### File: `cg_rera_extractor/parsing/data/logical_sections_and_keys.json`

#### Complete Updated Configuration:
```json
{
  "sections": [
    {
      "logical_section": "project_details",
      "section_title_variants": [
        "project details",
        "project information",
        "details of project",
        "general information",
        "project particulars"
      ],
      "keys": {
        "registration_number": ["registration number", "registration no", "project registration no", "rera reg no"],
        "project_name": ["project name", "name of project", "project title"],
        "project_type": ["project type", "type of project", "nature of project"],
        "project_status": ["project status", "current status", "status"],
        "district": ["district", "dist"],
        "tehsil": ["tehsil", "taluka", "block"],
        "village_or_locality": ["village", "locality", "mohalla", "ward", "sector", "colony"],
        "project_address": ["project address", "address of project", "site address", "location"],
        "project_website": ["project website", "website", "web", "url"],
        "pincode": ["pincode", "pin", "pin code", "postal code"],
        "total_units": ["total units", "total number of units", "no of units"],
        "total_area_sq_m": ["total area (sq m)", "project area", "total project area", "land area"],
        "launch_date": ["launch date", "start date", "commencement date", "project start"],
        "expected_completion_date": ["expected completion", "expected completion date", "proposed end date", "completion date", "project end date"]
      }
    },
    {
      "logical_section": "promoter_details",
      "section_title_variants": [
        "promoter information",
        "promoter details",
        "developer details",
        "builder details",
        "promoter particulars"
      ],
      "keys": {
        "promoter_name": ["promoter name", "name", "developer name", "builder name"],
        "promoter_type": ["promoter type", "application type", "organisation type", "org type", "type of entity", "entity type"],
        "promoter_address": ["promoter address", "address", "registered address", "office address", "correspondence address", "regd address"],
        "promoter_email": ["promoter email", "email", "email id", "e-mail"],
        "promoter_phone": ["promoter phone", "contact number", "mobile", "mob no", "phone no", "telephone", "contact"],
        "promoter_pan": ["promoter pan", "pan", "pan no", "pan number"],
        "promoter_cin": ["promoter cin", "cin", "cin no", "company cin"],
        "promoter_gst": ["gst", "gst number", "gstin", "gst no"]
      }
    }
  ]
}
```

---

## 6. Missing Retry & Deduplication Logic

### File: `cg_rera_extractor/db/loader.py`

#### Issue 6.1: No Deduplication on Child Tables
- **Lines**: 316-317
- **Problem**: Child tables are deleted and re-inserted every load
- **Impact**: Loses historical data
- **Fix**:
```python
# Instead of deleting, use upsert pattern
from sqlalchemy.dialects.postgresql import insert

def _upsert_promoters(session: Session, project_id: int, promoters: list):
    for p in promoters:
        stmt = insert(Promoter).values(
            project_id=project_id,
            promoter_name=p.name,
            email=p.email,
            # ... other fields
        ).on_conflict_do_update(
            index_elements=['project_id', 'promoter_name'],
            set_={
                'email': p.email,
                # ... other updatable fields
            }
        )
        session.execute(stmt)
```

#### Issue 6.2: No Error Recovery for Partial Loads
- **Lines**: 534-536
- **Problem**: If one project fails, the entire run fails
- **Fix**:
```python
# Already implemented (continue pattern), but add tracking
failed_projects = []
try:
    project_stats = _load_project(...)
except Exception as exc:
    logger.error(f"Failed to load {path.name}: {exc}")
    failed_projects.append((path.name, str(exc)))
    continue  # Don't re-raise

# Store failed projects in audit
audit.error_log = {'failed_projects': failed_projects}
```

---

## Summary of Files Requiring Changes

| File | Changes | Priority | Effort |
|------|---------|----------|--------|
| `parsing/data/logical_sections_and_keys.json` | Add key variants | High | Low |
| `parsing/mapper.py` | Date parsing, doc extraction | High | Medium |
| `db/loader.py` | scraped_at, provenance, price calc | High | Medium |
| `parsing/raw_extractor.py` | Pincode extraction, URL normalization | Medium | Low |
| `parsing/schema.py` | Add V1Metadata fields | Medium | Low |

---

## Implementation Order

1. **Week 1**: Update `logical_sections_and_keys.json` (immediate improvement)
2. **Week 1**: Fix date parsing in `mapper.py`
3. **Week 2**: Add `scraped_at` and fix provenance in `loader.py`
4. **Week 2**: Add pincode extraction
5. **Week 3**: Implement price-per-sqft computation
6. **Week 3**: Add deduplication logic
7. **Week 4**: Add document extraction from previews
8. **Week 4**: Add progress table parsing
