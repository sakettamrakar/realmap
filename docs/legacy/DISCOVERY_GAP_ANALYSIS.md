# Discovery & Trust Layer - Gap Analysis Report

## Executive Summary

Analysis of the current codebase against the **3-Point Discovery Standard (Points 24-26)** reveals:

| Point | Requirement | Current Status | Gap Severity |
|-------|------------|----------------|--------------|
| **24** | Structured Locality Tags | ❌ Not Implemented | HIGH |
| **25** | RERA Verification System | ⚠️ Partial | MEDIUM |
| **26** | Entity Enrichment & Knowledge Graph | ⚠️ Partial | MEDIUM |

---

## Point 24: Structured Locality Tags (Faceted Search)

### Current State
- **Search Mechanism**: Text-based filtering only
  - Location: `district` (dropdown), `tehsil` (text input)
  - Filters: `project_types[]`, `statuses[]`, `min_overall_score`
  - Price: `min_price`, `max_price`
  - Text: `name_contains` (fuzzy search on project name)
  
- **No Tag System Exists**:
  - No `Tag` entity in `models.py` or `models_enhanced.py`
  - No many-to-many `ProjectTags` join table
  - No proximity-based auto-tagging (e.g., "Hinjewadi-proximate")
  - No infrastructure tags (e.g., "Metro-connected", "Airport-access")
  - No investment tags (e.g., "High-Rental-Yield", "Pre-Launch")

- **Search Service** (`services/search.py`):
  ```python
  # Current filters are hardcoded field-based
  if params.district:
      stmt = stmt.filter(Project.district.ilike(params.district))
  if params.statuses:
      stmt = stmt.filter(Project.status.in_(params.statuses))
  ```

### Gap Analysis
| Requirement | Exists | Notes |
|-------------|--------|-------|
| `Tag` entity | ❌ | No tag model |
| `ProjectTags` join table | ❌ | No M2M relationship |
| Proximity tags (calculated) | ❌ | No distance-based tagging |
| Infrastructure tags | ❌ | No metro/airport linkage |
| Investment tags | ❌ | No pre-launch/yield tags |
| Keyword-indexed filters | ❌ | Text search only |
| Frontend checkbox filtering | ❌ | Only dropdowns exist |

### Required Implementation
1. Create `Tag` and `ProjectTag` models
2. Create tag taxonomy (proximity, infrastructure, investment)
3. Add auto-tagging service for proximity calculation
4. Add `tags` filter to SearchParams
5. Frontend: Add tag chips/checkboxes to FiltersSidebar

---

## Point 25: RERA Verification System (The Trust Badge)

### Current State
- **RERA ID Storage**: Plain text string
  ```python
  # models.py - Project
  rera_registration_number: Mapped[str] = mapped_column(String(100), nullable=False)
  ```

- **Partial Verification in Enhanced Models**:
  ```python
  # models_enhanced.py - TransactionHistory (NOT Project!)
  verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
  verification_status: Mapped[str | None] = mapped_column(String(30))
  ```

- **No Project-Level Verification**:
  - No `verification_status` enum on Project
  - No `official_record_link` URL field
  - No `last_verified_at` timestamp

- **API Schema Has Provenance** (`schemas_api.py`):
  ```python
  class DataProvenance(BaseModel):
      last_verified_at: datetime | None = None  # Field exists but not populated
  ```

### Gap Analysis
| Requirement | Exists | Notes |
|-------------|--------|-------|
| `rera_registration_number` | ✅ | Plain string |
| `verification_status` enum | ❌ | Not on Project model |
| `official_record_link` URL | ❌ | Not implemented |
| `last_verified_at` timestamp | ⚠️ | In TransactionHistory only |
| Verification enum (VERIFIED/PENDING/REVOKED/EXPIRED) | ❌ | No enum defined |
| Trust Badge UI component | ❌ | No green tick badge |
| Link to government portal | ❌ | No `rel=nofollow` link |

### Required Implementation
1. Add `ReraVerificationStatus` enum
2. Add verification fields to `Project` model
3. Create `generate_rera_verification_link()` function for CG RERA portal
4. Add trust badge to frontend ProjectDetail
5. Implement periodic verification check service

---

## Point 26: Entity Enrichment & Knowledge Graph

### Current State
- **Developer Entity**: ✅ Exists in enhanced models
  ```python
  # models_enhanced.py
  class Developer(Base):
      name: Mapped[str]
      trust_score: Mapped[Decimal | None]
      total_projects_completed: Mapped[int | None]
      # ... has relationship to DeveloperProject
  ```

- **Developer-Project Linking**: ✅ Exists
  ```python
  class DeveloperProject(Base):
      developer_id: Mapped[int] = mapped_column(ForeignKey("developers.id"))
      project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
  ```

- **BUT** Detail Service Returns `None`:
  ```python
  # services/detail.py line 108
  "developer": None,  # Not populated!
  ```

- **No Automatic Sibling Fetching**:
  - No "Other Projects by Developer" query
  - No "Related Projects" section in API response

- **No Landmark Linking**:
  - Amenity POIs exist but not linked as entities
  - No auto-linking "Near Phoenix Mall" to entity pages
  - No SEO-friendly internal linking structure

### Gap Analysis
| Requirement | Exists | Notes |
|-------------|--------|-------|
| Developer as entity | ✅ | In models_enhanced.py |
| Developer-Project relationship | ✅ | DeveloperProject table |
| Fetch developer in detail | ❌ | Returns `None` |
| "Other Projects by Developer" query | ❌ | Not implemented |
| Landmark entity | ⚠️ | AmenityPOI exists but not linked |
| Auto-link landmark text | ❌ | No entity linking |
| Internal link graph | ❌ | No interlinking structure |

### Required Implementation
1. Update `fetch_project_detail()` to populate developer info
2. Create `fetch_developer_projects()` service function
3. Add `related_projects` section to detail response
4. Create Landmark entity with SEO-friendly URLs
5. Implement text-to-entity linking for descriptions

---

## Database Schema Gaps Summary

### Missing Tables
```sql
-- Point 24: Tag System
CREATE TABLE tags (...)
CREATE TABLE project_tags (...)

-- Point 26: Landmark Entities
CREATE TABLE landmarks (...)
CREATE TABLE project_landmarks (...)
```

### Missing Columns
```sql
-- Point 25: RERA Verification (on projects table)
ALTER TABLE projects ADD COLUMN rera_verification_status VARCHAR(20);
ALTER TABLE projects ADD COLUMN rera_official_link VARCHAR(1024);
ALTER TABLE projects ADD COLUMN rera_last_verified_at TIMESTAMP WITH TIME ZONE;
```

---

## Search Index Gaps

### Current Indexing
- B-tree indexes on: `district`, `tehsil`, `status`, `approved_date`
- Score indexes: `overall_score`, `location_score`, `amenity_score`
- Spatial: `lat`, `lon` on project_locations

### Missing for Faceted Search
- No `keyword` type index for tags (Elasticsearch/Algolia)
- No facet aggregation in API responses
- No tag-based filtering in `SearchParams`

---

## API Endpoint Gaps

| Endpoint | Exists | Purpose |
|----------|--------|---------|
| `GET /projects/search` | ✅ | List with filters |
| `GET /projects/{id}` | ✅ | Project detail |
| `GET /projects/lookup/{identifier}` | ✅ | By ID or RERA |
| `GET /developers/{id}` | ❌ | Developer profile |
| `GET /developers/{id}/projects` | ❌ | Sibling projects |
| `GET /tags` | ❌ | Tag taxonomy |
| `GET /tags/{slug}/projects` | ❌ | Projects by tag |
| `GET /landmarks/{id}` | ❌ | Landmark entity |

---

## Implementation Priority

### Phase 1: Trust Layer (Point 25)
- High impact on user trust
- Low complexity (add fields + enum)
- Immediate SEO benefit

### Phase 2: Search Tags (Point 24)
- High impact on discoverability
- Medium complexity (new tables + service)
- Enables faceted navigation

### Phase 3: Knowledge Graph (Point 26)
- Medium impact on engagement
- High complexity (entity linking + NLP)
- Long-term SEO benefits

---

## Next Steps

1. **Create migration script** for Point 25 fields
2. **Define Tag taxonomy** CSV/JSON for Point 24
3. **Implement enrichment service** for Point 26 sibling fetching
4. **Update frontend** FiltersSidebar for tag checkboxes
5. **Add trust badge** component to ProjectDetail
