# Final Data Improvement Roadmap

> **Audit Date**: December 10, 2024  
> **Estimated Total Effort**: 8-12 weeks
> **Priority System**: P0 (Critical) → P3 (Nice to Have)

---

## Executive Summary

This roadmap prioritizes 47 identified data quality improvements across extraction, transformation, and storage layers. Improvements are organized by business impact and implementation complexity.

---

## Phase 1: Critical Fixes (Week 1-2)

### P0 - Data Loss Prevention

| ID | Issue | Impact | Effort | Owner |
|----|-------|--------|--------|-------|
| P0-1 | **Fix date parsing** for `approved_date`, `proposed_end_date` | Loses timeline data | 2 hours | ETL |
| P0-2 | **Set `scraped_at` timestamp** in loader | Loses freshness tracking | 1 hour | ETL |
| P0-3 | **Extract `village_or_locality`** from HTML | Loses locality data | 2 hours | Parser |
| P0-4 | **Extract `pincode`** from address | Loses postal data | 2 hours | Parser |
| P0-5 | **Fix document extraction** from previews | Loses document links | 4 hours | ETL |

**Acceptance Criteria**:
- All 5 fields populated for 100% of new scrapes
- Backfill existing 2 projects with corrected data

### P0 - QA Pipeline Activation

| ID | Issue | Impact | Effort | Owner |
|----|-------|--------|--------|-------|
| P0-6 | **Enable QA validation** in loader | No quality gates | 2 hours | ETL |
| P0-7 | **Populate `qa_flags` and `qa_status`** | No visibility into data quality | 2 hours | ETL |
| P0-8 | **Fix provenance record creation** (AttributeError) | Audit trail broken | 1 hour | ETL |

**Acceptance Criteria**:
- QA runs on every project load
- Provenance records created without errors

---

## Phase 2: High Priority Improvements (Week 3-4)

### P1 - Core Data Completeness

| ID | Issue | Impact | Effort | Owner |
|----|-------|--------|--------|-------|
| P1-1 | **Fix promoter field mapping** (type, phone, address) | 100% NULL for 3 fields | 2 hours | Parser |
| P1-2 | **Fix building section parsing** | 0 buildings captured | 4 hours | Parser |
| P1-3 | **Fix quarterly updates parsing** | 0 updates captured | 4 hours | Parser |
| P1-4 | **Add key variants to JSON config** | Low extraction coverage | 2 hours | Config |
| P1-5 | **Compute price_per_sqft by area type** | Missing price analysis | 4 hours | ETL |

**Acceptance Criteria**:
- Buildings extracted for projects with tower data
- Quarterly updates extracted when progress tables exist
- Price per sqft computed for all pricing snapshots

### P1 - Reference Data Seeding

| ID | Issue | Impact | Effort | Owner |
|----|-------|--------|--------|-------|
| P1-6 | **Seed amenity_categories** | Taxonomy scoring broken | 1 hour | Data |
| P1-7 | **Seed amenities** | No lifestyle scoring | 1 hour | Data |
| P1-8 | **Seed document_types** | No document classification | 1 hour | Data |

**Acceptance Criteria**:
- All lookup tables populated with standard values
- Amenity taxonomy can be used for scoring

---

## Phase 3: Schema Enhancements (Week 5-6)

### P2 - New Field Additions

| ID | Issue | Impact | Effort | Owner |
|----|-------|--------|--------|-------|
| P2-1 | **Add `project_website_url`** to projects | Missing marketing data | 2 hours | Schema |
| P2-2 | **Add building detail fields** (basement, parking, height) | Incomplete building data | 2 hours | Schema |
| P2-3 | **Add unit area breakdowns** (balcony, common, terrace) | Incomplete area data | 2 hours | Schema |
| P2-4 | **Add land parcel fields** (ward, mutation, plot) | Incomplete land data | 2 hours | Schema |
| P2-5 | **Add bank account fields** (type, funds) | Incomplete financial data | 2 hours | Schema |
| P2-6 | **Add progress percentages** to quarterly_updates | No milestone tracking | 2 hours | Schema |

**Acceptance Criteria**:
- All new columns created in database
- ORM models updated
- API schemas expose new fields

### P2 - Normalization

| ID | Issue | Impact | Effort | Owner |
|----|-------|--------|--------|-------|
| P2-7 | **Create localities table** | No location normalization | 4 hours | Schema |
| P2-8 | **Link projects to localities** | No faceted location search | 2 hours | Schema |
| P2-9 | **Create document_types lookup** | No document classification | 2 hours | Schema |
| P2-10 | **Link artifacts to document_types** | No document categorization | 2 hours | Schema |

---

## Phase 4: Score Computation (Week 7-8)

### P2 - Missing Scores

| ID | Issue | Impact | Effort | Owner |
|----|-------|--------|--------|-------|
| P2-11 | **Compute `amenity_score`** from onsite amenities | Missing quality metric | 8 hours | Scoring |
| P2-12 | **Compute `value_score`** from price-quality ratio | Missing value metric | 8 hours | Scoring |
| P2-13 | **Compute `lifestyle_score`** from taxonomy | Missing lifestyle metric | 8 hours | Scoring |

**Acceptance Criteria**:
- All 3 scores populated for projects with required data
- Scores validated against expected ranges

### P3 - Enhanced Scores

| ID | Issue | Impact | Effort | Owner |
|----|-------|--------|--------|-------|
| P3-1 | **Compute `safety_score`** | Nice to have | 8 hours | Scoring |
| P3-2 | **Compute `environment_score`** | Nice to have | 8 hours | Scoring |
| P3-3 | **Compute `investment_potential_score`** | Nice to have | 8 hours | Scoring |
| P3-4 | **Populate `structured_ratings` JSON** | Nice to have | 4 hours | Scoring |

---

## Phase 5: Advanced Features (Week 9-12)

### P2 - Entity Extraction

| ID | Issue | Impact | Effort | Owner |
|----|-------|--------|--------|-------|
| P2-14 | **Implement developer entity** promotion | No developer tracking | 16 hours | ETL |
| P2-15 | **Link developers to projects** | No developer reputation | 4 hours | ETL |
| P2-16 | **Seed landmark data** for CG | No landmark proximity | 8 hours | Data |
| P2-17 | **Compute landmark distances** | No proximity tags | 8 hours | Geo |

### P3 - Discovery Features

| ID | Issue | Impact | Effort | Owner |
|----|-------|--------|--------|-------|
| P3-5 | **Implement tagging service** | No faceted search | 16 hours | Backend |
| P3-6 | **Seed standard tags** | No predefined filters | 4 hours | Data |
| P3-7 | **Auto-apply proximity tags** | Manual tagging required | 8 hours | Backend |
| P3-8 | **Implement RERA verification** service | No trust badge | 16 hours | Backend |

### P3 - Future Features

| ID | Issue | Impact | Effort | Owner |
|----|-------|--------|--------|-------|
| P3-9 | **Individual unit tracking** | No inventory visibility | 24 hours | Schema+ETL |
| P3-10 | **Transaction history** integration | No price verification | 24 hours | Schema+ETL |
| P3-11 | **Possession timeline** tracking | No delay visibility | 16 hours | Schema+ETL |

---

## Cleanup & Deprecation (Ongoing)

### Columns to Deprecate

| Column | Table | Timeline | Migration Required |
|--------|-------|----------|-------------------|
| `geocoding_source` | projects | After Phase 2 | Merge to geo_source |
| `formatted_address` | projects | After Phase 2 | Merge to geo_formatted_address |
| `unit_types` (table) | - | After Phase 3 | Migrate to project_unit_types |
| `project_documents` (table) | - | Already done | Fully migrated |

### Tables to Remove

| Table | Timeline | Condition |
|-------|----------|-----------|
| `testabc` | Immediate | Test table, delete |

---

## Success Metrics

### Data Quality KPIs

| Metric | Current | Target | Phase |
|--------|---------|--------|-------|
| Projects NULL rate (core fields) | 44% | <10% | 1-2 |
| Promoters NULL rate | 50% | <20% | 2 |
| Buildings captured rate | 0% | >80% | 2 |
| Documents captured rate | 0% | >90% | 1 |
| QA coverage | 0% | 100% | 1 |
| Score completeness | 60% | >95% | 4 |

### Pipeline Health KPIs

| Metric | Current | Target | Phase |
|--------|---------|--------|-------|
| Provenance records per project | 0 | 1 | 1 |
| Ingestion audits per run | 0 | 1 | 1 |
| Average extraction confidence | Unknown | >0.8 | 2 |
| Fields extracted per project | ~10 | >25 | 3 |

---

## Resource Allocation

### Estimated Effort by Phase

| Phase | Duration | Effort (hours) | Resources |
|-------|----------|----------------|-----------|
| Phase 1: Critical | Week 1-2 | 16 hours | 1 dev |
| Phase 2: High Priority | Week 3-4 | 24 hours | 1 dev |
| Phase 3: Schema | Week 5-6 | 24 hours | 1 dev |
| Phase 4: Scoring | Week 7-8 | 40 hours | 1 dev |
| Phase 5: Advanced | Week 9-12 | 100 hours | 2 devs |

**Total**: ~200 developer hours over 12 weeks

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Website structure change | Medium | High | Version selectors, monitor changes |
| Migration breaks API | Low | High | Versioned API, backward compat |
| Scoring algorithm disputes | Medium | Medium | Document methodology, user feedback |
| Performance degradation | Low | Medium | Add indexes, query optimization |

---

## Immediate Next Steps

1. **Today**: Update `logical_sections_and_keys.json` with expanded key variants
2. **Tomorrow**: Fix date parsing in `mapper.py`
3. **This Week**: Enable QA validation, fix scraped_at, fix provenance
4. **Next Week**: Run full re-scrape with fixes, validate data quality
5. **Week 3+**: Begin schema enhancements

---

## Appendix: Quick Wins

These fixes require <1 hour each and have immediate impact:

1. Set `scraped_at = datetime.now()` in loader (1 line)
2. Add `gst_number` to promoter key mappings (1 line)
3. Add `village` to project_details key mappings (1 line)
4. Fix provenance `source_domain` default (1 line)
5. Delete `testabc` test table (1 SQL statement)

**Combined effort**: 30 minutes
**Combined impact**: +5% data completeness
