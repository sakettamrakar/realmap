# API Gap Analysis Report: 7-Point API Standard (Points 11–17)

**Analysis Date:** December 2025  
**Auditor:** Principal API Architect  
**Scope:** Backend Services and API Layer alignment with competitive analysis

---

## Executive Summary

| Point | Feature | Status | Gap Level |
|-------|---------|--------|-----------|
| 11 | Unified Project Identity API | 🟡 Partial | Medium |
| 12 | Rich Media & Asset Management | 🔴 Missing | High |
| 13 | Price Trends & Analytics | 🔴 Missing | High |
| 14 | Gated Brochure Access | 🔴 Missing | High |
| 15 | Embedded JSON-LD (SEO) | 🔴 Missing | High |
| 16 | API Discovery & Metadata | 🟡 Partial | Medium |
| 17 | Data Provenance | 🟡 Partial | Medium |

**Legend:** 🟢 Compliant | 🟡 Partial | 🔴 Missing

---

## Detailed Gap Analysis

### 11. Unified Project Identity API

**Requirement:** Create/Update `GET /projects/:identifier` to accept *either* `project_id` OR `rera_id`.

**Current State:**
- ✅ `GET /projects/{project_id}` exists (accepts internal DB ID only)
- ✅ `GET /projects/{state_code}/{rera_registration_number}` exists (accepts RERA ID)
- ❌ No unified endpoint accepting either format
- ❌ Response does NOT include full hierarchical tree (Project → Tower → Unit)

**Evidence:**
```python
# routes_projects.py
@router.get("/{project_id}", response_model=ProjectDetailV2)
def project_detail_endpoint(project_id: int, db=Depends(get_db)):
    ...

# app.py
@app.get("/projects/{state_code}/{rera_registration_number}", response_model=ProjectDetail)
def get_project_detail(state_code: str, rera_registration_number: str, ...):
    ...
```

**Action Required:**
- [ ] Create unified `GET /projects/{identifier}` that auto-detects ID type
- [ ] Add full hierarchical tree to response (Project → Buildings → Units)
- [ ] Optimize for SSR with single query response

---

### 12. Rich Media & Asset Management

**Requirement:** Media API must return array of objects with `{ type, url, width, height, filesize_kb, license_type }`.

**Current State:**
- ✅ `ProjectArtifact` model exists with basic fields (`category`, `artifact_type`, `file_path`, `source_url`, `file_format`)
- ❌ No `width`, `height`, `filesize_kb` fields
- ❌ No `license_type` field
- ❌ No dedicated media API endpoint
- ❌ Floorplans not linked to specific Unit Types

**Evidence:**
```python
# models.py - ProjectArtifact
category: Mapped[str | None]  # legal, technical, etc.
artifact_type: Mapped[str | None]  # reg_cert, building_plan
file_path: Mapped[str | None]
source_url: Mapped[str | None]
file_format: Mapped[str | None]  # pdf, jpg
is_preview: Mapped[bool]
# Missing: width, height, filesize_kb, license_type
```

**Action Required:**
- [ ] Add `width_px`, `height_px`, `filesize_kb`, `license_type` to `ProjectArtifact`
- [ ] Add `unit_type_id` foreign key for floorplan linking
- [ ] Create dedicated `GET /projects/{id}/media` endpoint
- [ ] Return structured array instead of URL strings

---

### 13. Price Trends & Analytics

**Requirement:** New `GET /analytics/price-trends` with time-series data.

**Current State:**
- ✅ `ProjectPricingSnapshot` model exists with `snapshot_date`, `min_price_total`, etc.
- ❌ No analytics endpoint
- ❌ No time-series aggregation
- ❌ No quarterly/monthly granularity support

**Evidence:**
```python
# models.py - ProjectPricingSnapshot stores historical prices
snapshot_date: Mapped[date]
min_price_total: Mapped[Numeric | None]
max_price_total: Mapped[Numeric | None]
min_price_per_sqft: Mapped[Numeric | None]
# Data exists but no API to query trends
```

**Action Required:**
- [ ] Create `GET /analytics/price-trends` endpoint
- [ ] Support params: `entity_id`, `timeframe` (5Y, 1Y), `granularity` (Quarterly, Monthly)
- [ ] Aggregate pricing snapshots into time-series
- [ ] Return `[{ period, avg_price, volume, change_pct }]`

---

### 14. Gated Brochure Access (Security)

**Requirement:** Implement lead-wall with time-limited signed URLs.

**Current State:**
- ✅ `ProjectDocument` model stores brochure URLs
- ✅ `ProjectArtifact` model stores document references
- ❌ URLs are directly exposed (no access control)
- ❌ No lead capture mechanism
- ❌ No signed URL generation

**Evidence:**
```python
# models.py - ProjectDocument
url: Mapped[str | None] = mapped_column(String(1024))
# Direct URL storage, no access layer
```

**Action Required:**
- [ ] Create `POST /access/brochure` endpoint
- [ ] Implement lead capture (email/phone consent)
- [ ] Generate time-limited signed URLs (S3 presigned or equivalent)
- [ ] Set 15-minute expiry
- [ ] Never expose direct bucket URLs in API responses

---

### 15. Embedded JSON-LD (SEO)

**Requirement:** Inject `schema_org` field with Google Structured Data.

**Current State:**
- ❌ No JSON-LD generation
- ❌ No structured data in API responses
- ❌ No Schema.org mappings

**Action Required:**
- [ ] Create JSON-LD generator for projects
- [ ] Map: `Project` → `Schema.Product` or `Schema.Residence`
- [ ] Include `AggregateRating` from scores
- [ ] Include `Offer` for pricing
- [ ] Add `schema_org` field to `ProjectDetailV2` response

---

### 16. API Discovery & Metadata (Developer DX)

**Requirement:** Standard response envelope with pagination and discovery.

**Current State:**
- ✅ `ProjectSearchResponse` has basic pagination (`page`, `page_size`, `total`)
- ❌ No `meta` envelope with `api_version`
- ❌ No `links` for HATEOAS navigation (`next`, `prev`, `self`)
- ❌ No `GET /api/meta` discovery endpoint

**Evidence:**
```python
# schemas.py - ProjectSearchResponse
class ProjectSearchResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[ProjectSearchItem]
# Missing: meta, links
```

**Action Required:**
- [ ] Create response envelope wrapper
- [ ] Add `meta: { limit, offset, total_count, api_version }`
- [ ] Add `links: { self, next, prev, first, last }`
- [ ] Create `GET /api/meta` listing all resources

---

### 17. Data Provenance (Trust Layer)

**Requirement:** Expose extraction metadata on record level.

**Current State:**
- ✅ `Project.scraped_at` exists
- ✅ `Project.last_parsed_at` exists
- ✅ `Project.data_quality_score` exists
- ❌ No `source_domain` field exposed
- ❌ No `extraction_method` field (scraper/manual/feed)
- ❌ No `confidence_score` for records
- ❌ Metadata not included in API responses

**Evidence:**
```python
# models.py - Project
scraped_at: Mapped[date | None]
last_parsed_at: Mapped[date | None]
data_quality_score: Mapped[int | None]
# Missing: source_domain, extraction_method exposed in API
```

**Action Required:**
- [ ] Add `source_domain`, `extraction_method` to model or derive from existing
- [ ] Create `DataProvenance` embedded schema
- [ ] Include in all project responses: `{ last_updated_at, source_domain, extraction_method, confidence_score }`

---

## Implementation Priority Matrix

| Priority | Point | Effort | Business Impact |
|----------|-------|--------|-----------------|
| P0 (Critical) | 14 - Gated Brochure | High | Lead capture, security |
| P0 (Critical) | 15 - JSON-LD | Medium | SEO, discoverability |
| P1 (High) | 13 - Price Trends | High | Analytics differentiator |
| P1 (High) | 11 - Unified API | Medium | Developer experience |
| P2 (Medium) | 16 - API Discovery | Low | Developer DX |
| P2 (Medium) | 17 - Provenance | Low | Trust, transparency |
| P3 (Low) | 12 - Rich Media | Medium | Enhanced listings |

---

## File Modification Plan

### New Files to Create
1. `cg_rera_extractor/api/routes_analytics.py` - Price trends endpoint
2. `cg_rera_extractor/api/routes_access.py` - Gated brochure endpoint  
3. `cg_rera_extractor/api/routes_discovery.py` - API meta endpoint
4. `cg_rera_extractor/api/schemas_api.py` - New DTOs (envelope, JSON-LD, etc.)
5. `cg_rera_extractor/api/services/analytics.py` - Price trends service
6. `cg_rera_extractor/api/services/access.py` - Signed URL service
7. `cg_rera_extractor/api/services/jsonld.py` - JSON-LD generator

### Files to Modify
1. `cg_rera_extractor/api/routes_projects.py` - Unified identifier lookup
2. `cg_rera_extractor/api/schemas.py` - Add provenance, enhance response models
3. `cg_rera_extractor/api/app.py` - Register new routers
4. `cg_rera_extractor/db/models.py` - Add media metadata fields

---

## Next Steps

1. **Step 2:** Define Request/Response DTOs for all missing endpoints
2. **Step 3:** Implement controller logic for Price Trends and Gated Brochure
3. **Step 4:** Add JSON-LD generation
4. **Step 5:** Wrap responses with envelope metadata
