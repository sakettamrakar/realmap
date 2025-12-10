# Missing Fields Report

> **Audit Date**: December 10, 2024  
> **Source Website**: rera.cg.gov.in (Chhattisgarh RERA Portal)

---

## Overview

This document identifies fields that are **present on the source website** but are either:
1. Not captured in the database schema
2. Captured but not extracted by the scraper
3. Extracted but not properly stored

---

## Fields Present on Website but Missing from Schema

### 1. Project Details Section

| Website Field | Current Status | Recommendation |
|--------------|----------------|----------------|
| `Project Website URL` | **NOT IN SCHEMA** | Add to `projects.project_website_url` |
| `Google Map Link` | **NOT IN SCHEMA** | Could be alternative geo source |
| `Number of Phases` | **NOT IN SCHEMA** | Add to `projects.number_of_phases` |
| `FSI Approved` | **NOT IN SCHEMA** | Add to `projects.fsi_approved` |
| `FAR Approved` | **NOT IN SCHEMA** | Add to `projects.far_approved` |
| `Litigations Pending` | **NOT IN SCHEMA** | Add to `projects.has_litigation` (boolean) |

### 2. Promoter Details Section

| Website Field | Current Status | Recommendation |
|--------------|----------------|----------------|
| `Promoter GST Number` | **NOT IN SCHEMA** | Add to `promoters.gst_number` |
| `Promoter Aadhaar (masked)` | **NOT IN SCHEMA** | Could add masked version for verification |
| `Authorized Signatory` | **NOT IN SCHEMA** | Add to `promoters.authorized_signatory` |
| `CA Certificate Details` | **NOT IN SCHEMA** | Add to `project_documents` |

### 3. Land Details Section

| Website Field | Current Status | Recommendation |
|--------------|----------------|----------------|
| `Ward Number` | **NOT IN SCHEMA** | Add to `land_parcels.ward_number` |
| `Mutation Number` | **NOT IN SCHEMA** | Add to `land_parcels.mutation_number` |
| `Patwari Halka` | **NOT IN SCHEMA** | Add to `land_parcels.patwari_halka` |
| `Plot Number` | **NOT IN SCHEMA** | Add to `land_parcels.plot_number` |
| `Open Space Area (sqmt)` | **NOT IN SCHEMA** | Add to `projects.open_space_area_sqmt` |
| `Approved Building Coverage` | **NOT IN SCHEMA** | Add to `projects.approved_building_coverage` |

### 4. Building/Tower Details Section

| Website Field | Current Status | Recommendation |
|--------------|----------------|----------------|
| `Basement Floors` | **NOT IN SCHEMA** | Add to `buildings.basement_floors` |
| `Stilt Floors` | **NOT IN SCHEMA** | Add to `buildings.stilt_floors` |
| `Podium Floors` | **NOT IN SCHEMA** | Add to `buildings.podium_floors` |
| `Building Height (meters)` | **NOT IN SCHEMA** | Add to `buildings.height_meters` |
| `Approved Building Plan Number` | **NOT IN SCHEMA** | Add to `buildings.plan_approval_number` |
| `Parking Slots` | **NOT IN SCHEMA** | Add to `buildings.parking_slots` |

### 5. Unit Details Section

| Website Field | Current Status | Recommendation |
|--------------|----------------|----------------|
| `Balcony Area (sqft)` | **NOT IN SCHEMA** | Add to `project_unit_types.balcony_area_sqft` |
| `Common Area (sqft)` | **NOT IN SCHEMA** | Add to `project_unit_types.common_area_sqft` |
| `Exclusive Terrace Area` | **NOT IN SCHEMA** | Add to `project_unit_types.terrace_area_sqft` |
| `Open Parking Price` | **NOT IN SCHEMA** | Add to `project_unit_types.open_parking_price` |
| `Covered Parking Price` | **NOT IN SCHEMA** | Add to `project_unit_types.covered_parking_price` |
| `Club Membership Fee` | **NOT IN SCHEMA** | Add to `project_unit_types.club_membership_fee` |

### 6. Bank/Financial Details

| Website Field | Current Status | Recommendation |
|--------------|----------------|----------------|
| `Bank Account Type` | **NOT IN SCHEMA** | Add to `bank_accounts.account_type` |
| `Authorized Signatories for Account` | **NOT IN SCHEMA** | Add to `bank_accounts.authorized_signatories` |
| `Total Funds Received` | **NOT IN SCHEMA** | Add to `bank_accounts.total_funds_received` |
| `Total Funds Utilized` | **NOT IN SCHEMA** | Add to `bank_accounts.total_funds_utilized` |

### 7. Approvals Section

| Website Field | Current Status | Recommendation |
|--------------|----------------|----------------|
| `Commencement Certificate` | Stored in previews | Normalize to `project_artifacts` |
| `Occupancy Certificate` | Stored in previews | Normalize to `project_artifacts` |
| `NOC - Fire` | Stored in previews | Normalize to `project_artifacts` |
| `NOC - Airport` | Stored in previews | Normalize to `project_artifacts` |
| `NOC - Environment` | Stored in previews | Normalize to `project_artifacts` |
| `Layout Approval` | Stored in previews | Normalize to `project_artifacts` |
| `Sanction Plan` | Stored in previews | Normalize to `project_artifacts` |

### 8. Progress/Timeline Section

| Website Field | Current Status | Recommendation |
|--------------|----------------|----------------|
| `Construction Start Date` | **NOT IN SCHEMA** | Add to `project_possession_timelines.construction_start` |
| `Revised Completion Date` | Stored as extended_end_date | Already in schema |
| `Phase-wise Timeline` | **NOT IN SCHEMA** | Need phase relationship |
| `% Foundation Complete` | **NOT IN SCHEMA** | Add to `quarterly_updates.foundation_percent` |
| `% Plinth Complete` | **NOT IN SCHEMA** | Add to `quarterly_updates.plinth_percent` |
| `% Superstructure Complete` | **NOT IN SCHEMA** | Add to `quarterly_updates.superstructure_percent` |
| `% MEP Complete` | **NOT IN SCHEMA** | Add to `quarterly_updates.mep_percent` |
| `% Finishing Complete` | **NOT IN SCHEMA** | Add to `quarterly_updates.finishing_percent` |

### 9. Amenities Section (On-site)

| Website Field | Current Status | Recommendation |
|--------------|----------------|----------------|
| `Internal Roads Status` | Captured in rera_locations | Link to `project_amenities` |
| `Internal Roads Image` | Partially captured | Store in `project_artifacts` |
| `Landscaping Status` | Captured in rera_locations | Link to `project_amenities` |
| `Community Hall` | **NOT EXTRACTED** | Add selector |
| `Swimming Pool Size` | **NOT IN SCHEMA** | Add to `project_amenities.size_details` |
| `Gym Equipment Details` | **NOT IN SCHEMA** | Add as JSON |

### 10. Complaint/Legal Section

| Website Field | Current Status | Recommendation |
|--------------|----------------|----------------|
| `Total Complaints Filed` | **NOT IN SCHEMA** | Add to `projects.total_complaints` |
| `Complaints Resolved` | **NOT IN SCHEMA** | Add to `projects.complaints_resolved` |
| `Orders Against Project` | **NOT IN SCHEMA** | Create `project_legal_orders` table |

---

## Fields Extracted but Not Stored

### From `raw_data.unmapped_sections`

| Raw Section | Sample Keys | Current Storage | Fix Required |
|-------------|-------------|-----------------|--------------|
| `Land Documents` | Encumbrance Certificate, Revenue Records | `raw_data_json` only | Parse to `project_artifacts` |
| `Approval From Competent Authoroties` | Building Permission, Fire NOC | `raw_data_json` only | Parse to `project_artifacts` |
| `Project Specific` | Site Map, Layout Plan | `raw_data_json` only | Parse to `project_artifacts` |
| `Acts & Rules` | RERA Act, Rules PDF | `raw_data_json` only | Not project-specific, ignore |
| `Segment Specific` | NA (usually empty) | `raw_data_json` only | Check if ever populated |

### From `previews` Dictionary

| Preview Key | Current Storage | Fix Required |
|-------------|-----------------|--------------|
| `registrationcertificate` | `notes` has path | Move to `project_artifacts` |
| `buildingplan` | `notes` has path | Move to `project_artifacts` |
| `approvedlayoutplan` | `notes` has path | Move to `project_artifacts` |
| `encumbrancecertificate` | `notes` has path | Move to `project_artifacts` |
| `revenuedocument` | `notes` has path | Move to `project_artifacts` |

---

## Fields with Format/Unit Issues

| Field | Current Format | Expected Format | Conversion Required |
|-------|----------------|-----------------|---------------------|
| `carpet_area_sqmt` | Square Meters (sqmt) | Also need sqft | Add sqft column or convert |
| `total_area_sq_m` | String sometimes | Float | Fix parser |
| `price_in_inr` | Sometimes with comma | Numeric | Already handled, verify |
| `launch_date` | DD/MM/YYYY or YYYY-MM-DD | ISO date | Parser handles, verify edge cases |
| `land_area` | Sometimes "Ha" (Hectares) | Square Meters | Add unit detection and conversion |

---

## Priority Recommendations

### High Priority (Data Loss Prevention)
1. **Extract and store document links**: Move from `previews.notes` to `project_artifacts`
2. **Parse unmapped sections**: Especially `Land Documents` and `Approvals`
3. **Add progress percentages**: Track construction milestones

### Medium Priority (Data Completeness)
1. **Add unit area breakdowns**: balcony, common area, terrace
2. **Add building details**: basement, stilt, parking
3. **Add land identifiers**: ward, mutation, patwari halka

### Low Priority (Nice to Have)
1. **Financial tracking**: funds received/utilized
2. **Complaint tracking**: requires separate data source
3. **Legal orders**: requires separate data source

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Fields on website, not in schema | **32** |
| Fields extracted, not stored | **12** |
| Fields with format issues | **5** |
| **Total missing/problematic fields** | **49** |
