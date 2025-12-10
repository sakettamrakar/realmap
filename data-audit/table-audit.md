# Table-by-Table Data Audit Report

> **Audit Date**: December 10, 2024  
> **Database**: PostgreSQL (realmap)  
> **Sample Size**: 2 projects in production

---

## Executive Summary

This audit identifies data quality issues across the RealMap database. Key findings:

1. **Critical**: Many columns are 100% NULL due to incomplete ETL pipeline
2. **High Priority**: Price-per-sqft by area type columns are not populated
3. **Medium**: Enhanced score columns (lifestyle, safety, environment) not computed
4. **Low**: Several lookup tables are empty (amenities taxonomy not seeded)

---

## Table: `projects` (2 rows)

| Column | Type | NULL Count | NULL % | Root Cause | Suggested Fix |
|--------|------|------------|--------|------------|---------------|
| `id` | integer | 0 | 0% | ✅ Primary key | N/A |
| `state_code` | varchar | 0 | 0% | ✅ Required | N/A |
| `rera_registration_number` | varchar | 0 | 0% | ✅ Required | N/A |
| `project_name` | varchar | 0 | 0% | ✅ Required | N/A |
| `status` | varchar | 0 | 0% | ✅ Extracted | N/A |
| `district` | varchar | 0 | 0% | ✅ Extracted | N/A |
| `tehsil` | varchar | 0 | 0% | ✅ Extracted | N/A |
| `village_or_locality` | varchar | **2** | **100%** | **Not extracted** | Add selector for locality in raw_extractor.py |
| `full_address` | varchar | 0 | 0% | ✅ Extracted | N/A |
| `pincode` | varchar | **2** | **100%** | **Not extracted** | Parse from address or add selector |
| `latitude` | numeric | 0 | 0% | ✅ Geocoded | N/A |
| `longitude` | numeric | 0 | 0% | ✅ Geocoded | N/A |
| `geocoding_status` | varchar | 0 | 0% | ✅ Set | N/A |
| `geocoding_source` | varchar | **2** | **100%** | Legacy field | Deprecate or populate from geo_source |
| `geo_source` | varchar | 0 | 0% | ✅ Set | N/A |
| `geo_precision` | varchar | 0 | 0% | ✅ Set | N/A |
| `geo_confidence` | numeric | **2** | **100%** | Not provided by geocoder | Add confidence from provider |
| `geo_normalized_address` | varchar | 0 | 0% | ✅ Set | N/A |
| `geo_formatted_address` | varchar | 0 | 0% | ✅ Set | N/A |
| `normalized_address` | varchar | 0 | 0% | ✅ Set | N/A |
| `formatted_address` | varchar | **2** | **100%** | Duplicate of geo_formatted_address | Remove or sync |
| `approved_date` | date | **2** | **100%** | **Extraction issue** | Fix date parsing in mapper.py |
| `proposed_end_date` | date | **2** | **100%** | **Extraction issue** | Fix date parsing in mapper.py |
| `extended_end_date` | date | **2** | **100%** | Not on website | Mark as optional |
| `raw_data_json` | json | 0 | 0% | ✅ Stored | N/A |
| `scraped_at` | timestamp | **2** | **100%** | **Not set in loader** | Set from metadata.scraped_at |
| `data_quality_score` | integer | **2** | **100%** | **Not computed** | Implement quality scorer |
| `last_parsed_at` | timestamp | 0 | 0% | ✅ Set | N/A |
| `qa_flags` | jsonb | **2** | **100%** | **QA not running** | Run QA validation in loader |
| `qa_status` | varchar | **2** | **100%** | **QA not running** | Run QA validation |
| `qa_last_checked_at` | timestamp | **2** | **100%** | **QA not running** | Run QA validation |

### Projects Table Issues Summary
- **Broken Extraction**: `village_or_locality`, `pincode`, `approved_date`, `proposed_end_date`
- **Missing Pipeline Step**: `scraped_at`, `data_quality_score`, `qa_*` fields
- **Legacy/Duplicate**: `geocoding_source`, `formatted_address`

---

## Table: `promoters` (2 rows)

| Column | Type | NULL Count | NULL % | Root Cause | Suggested Fix |
|--------|------|------------|--------|------------|---------------|
| `id` | integer | 0 | 0% | ✅ | N/A |
| `project_id` | integer | 0 | 0% | ✅ | N/A |
| `promoter_name` | varchar | 0 | 0% | ✅ Extracted | N/A |
| `promoter_type` | varchar | **2** | **100%** | **Not mapped** | Add "organisation_type" to key mappings |
| `email` | varchar | 0 | 0% | ✅ Extracted | N/A |
| `phone` | varchar | **2** | **100%** | **Not mapped** | Add "contact number" to key mappings |
| `address` | varchar | **2** | **100%** | **Not mapped** | Fix promoter_address mapping |
| `website` | varchar | **2** | **100%** | Not on website | Mark as optional |

### Promoters Table Issues Summary
- **Broken Mapping**: `promoter_type`, `phone`, `address` keys not matching HTML labels

---

## Table: `project_pricing_snapshots` (8 rows)

| Column | Type | NULL Count | NULL % | Root Cause | Suggested Fix |
|--------|------|------------|--------|------------|---------------|
| `id` | integer | 0 | 0% | ✅ | N/A |
| `project_id` | integer | 0 | 0% | ✅ | N/A |
| `snapshot_date` | date | 0 | 0% | ✅ | N/A |
| `unit_type_label` | varchar | 0 | 0% | ✅ | N/A |
| `min_price_total` | numeric | 0 | 0% | ✅ | N/A |
| `max_price_total` | numeric | 0 | 0% | ✅ | N/A |
| `min_price_per_sqft` | numeric | 1 | 12.5% | Division by zero guard | Add area fallback |
| `max_price_per_sqft` | numeric | 1 | 12.5% | Division by zero guard | Add area fallback |
| `source_type` | varchar | 0 | 0% | ✅ | N/A |
| `source_reference` | varchar | 0 | 0% | ✅ | N/A |
| `raw_data` | json | **8** | **100%** | **Never populated** | Store source data |
| `is_active` | boolean | 0 | 0% | ✅ | N/A |
| `created_at` | timestamp | 0 | 0% | ✅ | N/A |
| `price_per_sqft_carpet_min` | numeric | **8** | **100%** | **Not computed** | Implement carpet area calc |
| `price_per_sqft_carpet_max` | numeric | **8** | **100%** | **Not computed** | Implement carpet area calc |
| `price_per_sqft_sbua_min` | numeric | **8** | **100%** | **Not computed** | Implement SBUA calc |
| `price_per_sqft_sbua_max` | numeric | **8** | **100%** | **Not computed** | Implement SBUA calc |

### Pricing Snapshots Issues Summary
- **Not Implemented**: All `price_per_sqft_*_min/max` columns require ETL enhancement

---

## Table: `project_scores` (2 rows)

| Column | Type | NULL Count | NULL % | Root Cause | Suggested Fix |
|--------|------|------------|--------|------------|---------------|
| `id` | integer | 0 | 0% | ✅ | N/A |
| `project_id` | integer | 0 | 0% | ✅ | N/A |
| `connectivity_score` | integer | 0 | 0% | ✅ Computed | N/A |
| `daily_needs_score` | integer | 0 | 0% | ✅ Computed | N/A |
| `social_infra_score` | integer | 0 | 0% | ✅ Computed | N/A |
| `overall_score` | numeric | 0 | 0% | ✅ Computed | N/A |
| `location_score` | numeric | 0 | 0% | ✅ Computed | N/A |
| `score_version` | varchar | 0 | 0% | ✅ | N/A |
| `last_computed_at` | timestamp | 0 | 0% | ✅ | N/A |
| `score_status` | varchar | 0 | 0% | ✅ | N/A |
| `score_status_reason` | jsonb | 0 | 0% | ✅ | N/A |
| `amenity_score` | numeric | **2** | **100%** | **Not computed** | Implement onsite scoring |
| `value_score` | numeric | **2** | **100%** | **Not computed** | Implement price-quality ratio |
| `lifestyle_score` | numeric | **2** | **100%** | **Not computed** | Implement amenity taxonomy |
| `safety_score` | numeric | **2** | **100%** | **Not computed** | Implement safety scoring |
| `environment_score` | numeric | **2** | **100%** | **Not computed** | Implement environment scoring |
| `investment_potential_score` | numeric | **2** | **100%** | **Not computed** | Implement investment calc |
| `structured_ratings` | jsonb | **2** | **100%** | **Not computed** | Aggregate all sub-scores |

### Scores Table Issues Summary
- **Not Implemented**: 7 enhanced score columns need scoring algorithms

---

## Tables with 0 Rows (Empty)

| Table | Purpose | Status | Action Required |
|-------|---------|--------|-----------------|
| `amenities` | Amenity taxonomy | **Not seeded** | Seed reference data |
| `amenity_categories` | Category taxonomy | **Not seeded** | Seed reference data |
| `amenity_types` | Type variants | **Not seeded** | Seed reference data |
| `buildings` | Tower details | **Extraction broken** | Fix building section parsing |
| `data_provenance` | Audit trail | **Not implemented** | Enable in loader |
| `developer_projects` | Dev-Project link | **Not implemented** | Implement developer entity |
| `developers` | Developer entity | **Not implemented** | Implement developer extraction |
| `ingestion_audits` | Run tracking | **Not implemented** | Enable ingestion audit |
| `land_parcels` | Land details | **Extraction broken** | Fix land section parsing |
| `landmarks` | Known landmarks | **Not seeded** | Seed landmark data |
| `project_amenities` | Onsite amenities | **Not implemented** | Implement amenity linking |
| `project_documents` | Legacy docs table | **Deprecated** | Migrate to project_artifacts |
| `project_landmarks` | Proximity links | **Not implemented** | Implement landmark proximity |
| `project_possession_timelines` | Timeline tracking | **Not implemented** | Implement timeline extraction |
| `project_tags` | Project tags | **Not implemented** | Implement tagging service |
| `quarterly_updates` | Progress updates | **Extraction broken** | Fix quarterly section parsing |
| `rera_verifications` | RERA verification | **Not implemented** | Implement verification service |
| `tags` | Tag definitions | **Not seeded** | Seed tag data |
| `transaction_history` | Registry data | **Not implemented** | Future feature |
| `unit_types` | Legacy unit table | **Mostly empty** | Migrate to project_unit_types |
| `units` | Individual units | **Not implemented** | Future feature |

---

## Data Quality Statistics

### Overall Null Rate by Critical Tables

| Table | Total Columns | Columns with >50% NULL | Severity |
|-------|---------------|------------------------|----------|
| projects | 32 | 14 (44%) | **HIGH** |
| promoters | 8 | 4 (50%) | **MEDIUM** |
| project_pricing_snapshots | 17 | 5 (29%) | **MEDIUM** |
| project_scores | 17 | 7 (41%) | **HIGH** |

### Empty Tables Breakdown

- **Reference Data (needs seeding)**: 5 tables
- **ETL Not Implemented**: 10 tables
- **Extraction Broken**: 4 tables
- **Future Features**: 2 tables

---

## Recommendations

### Critical (Fix Immediately)
1. Fix date parsing for `approved_date` and `proposed_end_date`
2. Extract `village_or_locality` and `pincode` from HTML
3. Set `scraped_at` timestamp in loader
4. Enable QA validation during load

### High Priority
1. Implement price_per_sqft calculations by area type
2. Compute `amenity_score` from onsite amenities
3. Fix building and quarterly update extraction
4. Seed amenity taxonomy reference data

### Medium Priority
1. Implement developer entity promotion
2. Add landmark proximity calculations
3. Implement tagging service
4. Enable data provenance tracking

### Low Priority
1. Implement enhanced scores (lifestyle, safety, environment)
2. Add transaction history support
3. Implement individual unit tracking
