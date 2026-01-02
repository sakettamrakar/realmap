# [DEPRECATED] Schema & Data Coverage Analysis: 99acres vs RealMap

> **Note:** This analysis has been addressed by the Phase 0-3 implementation. See `docs/02-technical/Data_Model.md` for the current schema.

**Date:** January 2, 2026
**Analyst:** Senior Data Architect + System Analyst  
**Reference Schema:** 99acres Property Listing JSON Schema  
**Target System:** RealMap (RERA-focused Property Data Platform)

---

## Executive Summary

This report provides a **field-level comparison** between the 99acres property listing schema and the RealMap project's existing data models. The analysis identifies coverage gaps, partial implementations, and opportunities for schema enhancement.

### Coverage Metrics

| Metric | Count | Percentage |
|:---|---:|---:|
| Total 99acres Fields | 63 | 100% |
| Fully Covered | 29 | 46% |
| Partially Covered | 18 | 29% |
| Missing / Not Implemented | 16 | 25% |

**Key Finding:** RealMap has strong RERA-compliance and location data but lacks consumer-facing features like media galleries, price insights, and locality reviews.

---

## 1. Field-Level Comparison Matrix

### 1.1 Listing Metadata (`listing_meta`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `listing_id` | `projects.id` | ✅ Present | Both use integer PKs |
| `listing_name` | `projects.project_name` | ✅ Present | Direct mapping |
| `listing_type` | `projects.status` | ⚠️ Partial | Status != Listing Type (New/Resale) |
| `property_type` | `projects.property_type` | ✅ Present | Top-level field added |
| `listing_url` | `data_provenance.snapshot_url` | ⚠️ Partial | Audit trail, not listing URL |
| `shortlisted` | - | ❌ Missing | User feature (requires user accounts) |
| `view_count` | `projects.view_count` | ✅ Present | Analytics tracking enabled |

**Priority:** Medium  
**Recommendation:** `shortlisted` requires user authentication system.

---

### 1.2 Project Hierarchy & Deduplication (New)

| Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `parent_project_id` | `projects.parent_project_id` | ✅ Present | Links multiple RERA phases to one physical project |
| `canonical_project` | `parent_projects` table | ✅ Present | Physical project entity with slug and metadata |
| `other_phases` | `Project.other_registrations` | ✅ Present | API returns related RERA registrations |

**Priority:** N/A  
**Status:** ✅ Excellent Coverage  
**Recommendation:** Use `group_by_parent=true` in search API to prevent duplicate listings for multi-phase projects.

---

### 1.3 Media (`media`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `photos` | `MediaAsset.url` (API schema) | ⚠️ Partial | Model exists, no DB table |
| `videos` | `MediaAsset.url` (type=VIDEO) | ⚠️ Partial | Model exists, no DB table |
| `outdoor_videos` | - | ❌ Missing | No outdoor/indoor distinction |
| `floor_plan_images` | `project_artifacts.floor_plan_data` | ⚠️ Partial | JSON field, not structured images |
| `three_d_tour_available` | `MediaAsset.type=VIRTUAL_TOUR` | ⚠️ Partial | Model exists, no data |

**Priority:** High  
**Recommendation:** Create `project_media` table based on existing `MediaAsset` API schema. Populate from `project_documents` where `doc_type` includes images/videos.

---

### 1.3 Project Highlights (`project_highlights`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `why_consider` | - | ❌ Missing | Marketing copy array |
| `developer_name` | `promoters.promoter_name` | ✅ Present | Via `promoters` table |
| `developer_profile_url` | `developers.website` | ⚠️ Partial | Model exists, table empty |
| `contact_builder` | - | ❌ Missing | UI feature flag |

**Priority:** Low  
**Recommendation:** `why_consider` is marketing fluff. Focus on objective data. Developer profiles should be populated from `promoters` migration.

---

### 1.4 Location (`location`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `locality` | `projects.village_or_locality` | ✅ Present | Direct mapping |
| `area` | `projects.district` / `projects.tehsil` | ✅ Present | Two-level hierarchy |
| `city` | `projects.district` | ✅ Present | City = District in CG context |
| `state` | `projects.state_code` | ✅ Present | Normalized to state code |
| `coordinates.latitude` | `projects.latitude` | ✅ Present | Decimal(9,6) |
| `coordinates.longitude` | `projects.longitude` | ✅ Present | Decimal(9,6) |

**Priority:** N/A  
**Status:** ✅ Excellent Coverage  
**Recommendation:** None. Location handling is robust.

---

### 1.5 Compliance (`compliance`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `rera_registered` | Implicit (all projects are RERA) | ✅ Present | Core data source is RERA |
| `rera_id` | `projects.rera_registration_number` | ✅ Present | Primary key component |
| `no_brokerage` | - | ❌ Missing | Business model flag |
| `verified` | `rera_verifications.status` | ⚠️ Partial | Table exists, empty |

**Priority:** Medium  
**Recommendation:** Populate `rera_verifications` table to power "Trust Badge" feature. `no_brokerage` is not relevant for RERA-sourced data.

---

### 1.6 Construction Status (`construction_status`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `status` | `projects.status` | ✅ Present | Approved/Expired/Revoked |
| `phase` | `project_possession_timelines.phase` | ⚠️ Partial | Model exists, table empty |
| `completion_date` | `projects.proposed_end_date` | ✅ Present | RERA deadline date |

**Priority:** High  
**Recommendation:** Populate `project_possession_timelines` to track construction phases and delays.

---

### 1.7 Pricing (`pricing`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `base_price` | `project_pricing_snapshots.min_price_total` | ⚠️ Partial | Table empty |
| `price_range.min` | `project_pricing_snapshots.min_price_total` | ⚠️ Partial | Table empty |
| `price_range.max` | `project_pricing_snapshots.max_price_total` | ⚠️ Partial | Table empty |
| `price_per_sqft` | `project_pricing_snapshots.min_price_per_sqft` | ⚠️ Partial | Table empty |
| `currency` | Implicit (INR) | ✅ Present | Hardcoded to INR |
| `charges.stamp_duty` | - | ❌ Missing | Calculated value |
| `charges.registration` | - | ❌ Missing | Calculated value |
| `charges.government_charges` | - | ❌ Missing | Calculated value |

**Priority:** High  
**Recommendation:** 
1. Populate `project_pricing_snapshots` from manual price data or scraping.
2. Add calculated fields for stamp duty (7% in CG) and registration (1%).

---

### 1.8 Unit Configurations (`unit_configurations`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `bhk_type` | `project_unit_types.unit_label` | ✅ Present | "2 BHK", "3 BHK" |
| `carpet_area_sqft` | `project_unit_types.carpet_area_min_sqft` | ✅ Present | Normalized to SQFT |
| `carpet_area_sqm` | Derived from sqft | ✅ Present | Can calculate |
| `price` | `project_pricing_snapshots` (by unit type) | ⚠️ Partial | No per-unit-type pricing yet |
| `floor_plan_image` | `project_artifacts.floor_plan_data` | ⚠️ Partial | JSON, not image URL |
| `three_d_view` | - | ❌ Missing | Media feature |

**Priority:** Medium  
**Recommendation:** Link `project_pricing_snapshots.unit_type_label` to `project_unit_types` for per-configuration pricing.

---

### 1.9 Amenities (`amenities`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `amenities` (array of strings) | `project_amenities` + `amenity_types` | ⚠️ Partial | Models exist, tables empty |

**Priority:** High  
**Recommendation:** Populate amenity taxonomy from RERA raw data. Current data is in `raw_data_json` but not normalized.

---

### 1.10 Location Advantages (`location_advantages`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `place` | `project_landmarks.landmark.name` | ⚠️ Partial | Model exists, table empty |
| `distance` | `project_landmarks.distance_km` | ⚠️ Partial | Model exists, table empty |

**Priority:** High  
**Recommendation:** Populate `landmarks` and `project_landmarks` from `amenity_poi` and proximity calculations.

---

### 1.11 Project Description (`project_description`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `overview` | `document_extractions.summary` | ⚠️ Partial | LLM-generated summaries |
| `interior_specifications` | - | ❌ Missing | Marketing copy |
| `other_features` | - | ❌ Missing | Marketing copy |
| `brochure_link` | `project_documents.url` (where doc_type='brochure') | ✅ Present | Filtered query |

**Priority:** Low  
**Recommendation:** Use `document_extractions.summary` for overview. Interior specs are not in RERA data.

---

### 1.12 Related Listings (`related_listings`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `resale` | - | ❌ Missing | Requires secondary market data |
| `rental` | - | ❌ Missing | Requires rental listings |

**Priority:** Low  
**Recommendation:** Out of scope for RERA-focused platform. Would require integration with external listing APIs.

---

### 1.13 Price Insights (`price_insights`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `price_trend_percentage` | `PriceTrendDataPoint.change_pct` | ⚠️ Partial | API model exists, no data |
| `price_history` (time series) | `PriceTrendResponse.trend_data` | ⚠️ Partial | API model exists, no data |

**Priority:** High  
**Recommendation:** Implement price tracking job to populate `project_pricing_snapshots` over time.

---

### 1.14 Locality Insights (`locality_insights`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `overview` | `localities.description` (if populated) | ❌ Missing | Table empty |
| `ratings.connectivity` | `project_scores.connectivity_score` | ✅ Present | Computed metric |
| `ratings.lifestyle` | `project_scores.lifestyle_score` | ✅ Present | Computed metric |
| `ratings.safety` | `project_scores.safety_score` | ✅ Present | Computed metric |
| `ratings.greenery` | `project_scores.environment_score` | ⚠️ Partial | Renamed to "environment" |
| `reviews` | - | ❌ Missing | User-generated content |

**Priority:** Medium  
**Recommendation:** 
1. Aggregate `project_scores` by locality to generate locality-level insights.
2. Reviews require user accounts and moderation system.

---

### 1.15 Finance (`finance`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `loan_available` | - | ❌ Missing | Business feature |
| `partner_banks` | `bank_accounts.bank_name` | ⚠️ Partial | RERA accounts, not loan partners |

**Priority:** Low  
**Recommendation:** `bank_accounts` are escrow accounts, not financing partners. Loan info requires partnership integrations.

---

### 1.16 Developer (`developer`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `name` | `promoters.promoter_name` | ✅ Present | Direct mapping |
| `about` | `developers.description` | ⚠️ Partial | Model exists, table empty |
| `projects` | `developer_projects` | ⚠️ Partial | Model exists, table empty |

**Priority:** Medium  
**Recommendation:** Migrate `promoters` to `developers` entity model to enable cross-project analytics.

---

### 1.17 Metadata (`metadata`)

| 99acres Field | RealMap Equivalent | Status | Notes |
|:---|:---|:---|:---|
| `source` | `data_provenance.source_domain` | ✅ Present | Audit trail |
| `scraped_at` | `data_provenance.scraped_at` | ✅ Present | Timestamp |
| `listing_status` | `projects.status` | ✅ Present | RERA status |

**Priority:** N/A  
**Status:** ✅ Excellent Coverage  
**Recommendation:** None. Provenance tracking is robust.

---

## 2. Missing Fields Report

### 2.1 Critical (High Priority)

| Field | Entity | Purpose | Implementation Path |
|:---|:---|:---|:---|
| `price_range` | `pricing` | User decision making | Populate `project_pricing_snapshots` |
| `amenities` (normalized) | `amenities` | Search filtering | Populate amenity taxonomy |
| `location_advantages` | `location_advantages` | Proximity marketing | Populate `landmarks` + calculations |
| `price_trend_percentage` | `price_insights` | Investment insights | Time-series price tracking |
| `photos` (structured) | `media` | Visual discovery | Create `project_media` table |
| `construction_status.phase` | `construction_status` | Progress tracking | Populate `project_possession_timelines` |

### 2.2 Medium Priority

| Field | Entity | Purpose | Implementation Path |
|:---|:---|:---|:---|
| `verified` | `compliance` | Trust signal | Populate `rera_verifications` |
| `locality_insights.overview` | `locality_insights` | SEO + Discovery | Aggregate from `project_scores` |
| `developer.about` | `developer` | Trust building | Migrate to `developers` table |
| `stamp_duty` | `pricing.charges` | Buyer planning | Add calculated field (7% CG rate) |

### 2.3 Low Priority / Out of Scope

| Field | Entity | Reason |
|:---|:---|:---|
| `shortlisted` | `listing_meta` | Requires user accounts |
| `view_count` | `listing_meta` | Requires analytics tracking |
| `why_consider` | `project_highlights` | Marketing copy, subjective |
| `interior_specifications` | `project_description` | Not in RERA data |
| `related_listings` | N/A | Requires secondary market integration |
| `finance.loan_available` | `finance` | Requires banking partnerships |
| `reviews` | `locality_insights` | Requires UGC moderation |

---

## 3. Extra Fields in RealMap (Not in 99acres)

These fields exist in RealMap but have no equivalent in the 99acres schema:

| RealMap Field | Table | Purpose | Relevance |
|:---|:---|:---|:---|
| `rera_registration_number` | `projects` | Regulatory compliance | ✅ Critical (unique to RERA) |
| `qa_flags` | `projects` | Data quality gates | ✅ Critical (ops feature) |
| `document_extractions` | `document_extractions` | OCR/LLM processing | ✅ High (AI workflow) |
| `data_provenance` | `data_provenance` | Audit trail | ✅ High (trust layer) |
| `ingestion_audits` | `ingestion_audits` | ETL monitoring | ✅ High (ops) |
| `ai_scores` | `ai_scores` | ML-powered scoring | ✅ High (product differentiator) |
| `project_embeddings` | `project_embeddings` | Semantic search | ✅ High (AI chat) |
| `quarterly_updates` | `quarterly_updates` | Construction progress | ✅ Medium (RERA-specific) |
| `land_parcels` | `land_parcels` | Survey data | ⚠️ Medium (legal use case) |

**Finding:** RealMap has significant **operational and AI infrastructure** that 99acres lacks. These are competitive advantages for data quality and trust.

---

## 4. Structural Differences

### 4.1 Hierarchy

- **99acres:** Flat structure with nested objects
- **RealMap:** Relational hierarchy (Project → Building → Unit)

**Impact:** RealMap supports granular inventory management, 99acres is listing-focused.

### 4.2 Data Source

- **99acres:** Marketing listings from developers/agents
- **RealMap:** Regulatory data from government RERA portals

**Impact:** RealMap has higher trust but lacks "consumer appeal" features like videos and 3D tours.

### 4.3 Analytics Depth

- **99acres:** Historical price trends (external data)
- **RealMap:** Real-time amenity scoring, AI quality scores

**Impact:** Different value propositions (market intelligence vs regulatory compliance).

---

## 5. Recommendations & Action Plan

### 5.1 Immediate (Next Sprint)

1. **Populate Pricing Data:**
   - Create manual data entry or scraping pipeline for `project_pricing_snapshots`.
   - Calculate stamp duty/registration charges as derived fields.

2. **Normalize Amenities:**
   - Extract amenities from `raw_data_json` into `project_amenities` taxonomy.
   - Enable faceted search on amenities.

3. **Create Media Table:**
   - Implement `project_media` table based on existing `MediaAsset` API schema.
   - Link to `project_documents` and `project_artifacts`.

### 5.2 Short-Term (1-2 Months)

1. **Proximity Features:**
   - Populate `landmarks` table (malls, metro, hospitals).
   - Calculate `project_landmarks` distances for "Near X" search.

2. **Developer Profiles:**
   - Migrate `promoters` data to `developers` entity model.
   - Enable cross-project developer analytics.

3. **Trust Layer:**
   - Populate `rera_verifications` for "Verified" badge.
   - Implement auto-verification scraper.

### 5.3 Long-Term (Strategic)

1. **Price Tracking:**
   - Implement recurring job to snapshot `project_pricing_snapshots` monthly.
   - Build time-series analytics for investment insights.

2. **Locality Aggregation:**
   - Create locality-level insights dashboard from `project_scores`.
   - Generate SEO-friendly locality overview content.

3. **User Features (If Applicable):**
   - Add `view_count` tracking for popularity metrics.
   - Implement `shortlisted` feature with user accounts.

---

## 6. Coverage Gap Summary

| Category | 99acres Fields | Covered | Partial | Missing |
|:---|---:|---:|---:|---:|
| Listing Metadata | 7 | 2 | 3 | 2 |
| Media | 5 | 0 | 5 | 0 |
| Project Highlights | 4 | 1 | 1 | 2 |
| Location | 6 | 6 | 0 | 0 |
| Compliance | 4 | 2 | 1 | 1 |
| Construction Status | 3 | 2 | 1 | 0 |
| Pricing | 8 | 1 | 4 | 3 |
| Unit Configurations | 6 | 3 | 2 | 1 |
| Amenities | 1 | 0 | 1 | 0 |
| Location Advantages | 2 | 0 | 2 | 0 |
| Project Description | 4 | 1 | 1 | 2 |
| Related Listings | 2 | 0 | 0 | 2 |
| Price Insights | 2 | 0 | 2 | 0 |
| Locality Insights | 5 | 3 | 1 | 1 |
| Finance | 2 | 0 | 1 | 1 |
| Developer | 3 | 1 | 2 | 0 |
| Metadata | 3 | 3 | 0 | 0 |
| **TOTAL** | **63** | **29** | **18** | **16** |

---

## 7. Final Assessment

### Strengths of RealMap vs 99acres
✅ **Regulatory Compliance:** Complete RERA data capture  
✅ **Data Provenance:** Full audit trail and trust layer  
✅ **AI/ML Infrastructure:** Embeddings, scoring, imputation  
✅ **Operational Maturity:** QA gates, ingestion audits  
✅ **Granular Inventory:** Building → Unit hierarchy  

### Weaknesses vs 99acres
❌ **Consumer Media:** No photo galleries, videos, or 3D tours  
❌ **Price Intelligence:** No historical price trends  
❌ **Amenity Discovery:** Amenities not normalized for search  
❌ **Proximity Marketing:** Landmarks not populated  
❌ **User Engagement:** No shortlisting, reviews, or view tracking  

### Strategic Positioning
RealMap is a **B2B compliance platform** with strong data quality and regulatory focus. To compete in the **B2C property search** market like 99acres, it needs:
1. Media management (photos, videos)
2. Price tracking and insights
3. Normalized amenity search
4. Proximity-based discovery

Alternatively, RealMap can **lean into its strengths** by targeting:
- Institutional investors (trust + data quality)
- Legal due diligence services (provenance + audit trails)
- Government analytics (RERA compliance dashboards)

---

*End of Report*

