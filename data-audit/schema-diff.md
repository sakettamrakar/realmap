# Schema Diff Report

> **Date**: December 10, 2024  
> **Migration**: V001_data_audit_schema_upgrade

---

## Summary

This document shows the before/after comparison of the database schema following the data audit migration.

---

## Table: `projects`

### Before (32 columns)
```sql
id, state_code, rera_registration_number, project_name, status,
district, tehsil, village_or_locality, full_address, normalized_address,
pincode, latitude, longitude, geocoding_status, geocoding_source,
geo_source, geo_precision, geo_confidence, geo_normalized_address,
geo_formatted_address, approved_date, proposed_end_date, extended_end_date,
raw_data_json, scraped_at, data_quality_score, last_parsed_at,
qa_flags, qa_status, qa_last_checked_at, formatted_address
```

### After (42 columns)
```sql
-- Original columns (32)
id, state_code, rera_registration_number, project_name, status,
district, tehsil, village_or_locality, full_address, normalized_address,
pincode, latitude, longitude, geocoding_status, geocoding_source,
geo_source, geo_precision, geo_confidence, geo_normalized_address,
geo_formatted_address, approved_date, proposed_end_date, extended_end_date,
raw_data_json, scraped_at, data_quality_score, last_parsed_at,
qa_flags, qa_status, qa_last_checked_at, formatted_address,

-- NEW columns (+10)
project_website_url VARCHAR(1024),      -- Project marketing website URL
number_of_phases INTEGER DEFAULT 1,      -- Number of project phases
fsi_approved NUMERIC(6,2),              -- Floor Space Index approved
far_approved NUMERIC(6,2),              -- Floor Area Ratio approved
has_litigation BOOLEAN DEFAULT FALSE,   -- Pending litigations flag
open_space_area_sqmt NUMERIC(14,2),     -- Open space in sqm
approved_building_coverage NUMERIC(6,2), -- Building coverage %
total_complaints INTEGER DEFAULT 0,      -- Complaints filed
complaints_resolved INTEGER DEFAULT 0,   -- Complaints resolved
locality_id INTEGER                      -- FK to localities table
```

### New Indexes
```sql
CREATE INDEX ix_projects_has_litigation ON projects(has_litigation);
CREATE INDEX ix_projects_locality_id ON projects(locality_id);
```

---

## Table: `promoters`

### Before (8 columns)
```sql
id, project_id, promoter_name, promoter_type, email, phone, address, website
```

### After (10 columns)
```sql
-- Original (8)
id, project_id, promoter_name, promoter_type, email, phone, address, website,

-- NEW (+2)
gst_number VARCHAR(20),              -- GST registration number
authorized_signatory VARCHAR(255)    -- Authorized signatory name
```

---

## Table: `buildings`

### Before (7 columns)
```sql
id, project_id, building_name, building_type, number_of_floors, total_units, status
```

### After (14 columns)
```sql
-- Original (7)
id, project_id, building_name, building_type, number_of_floors, total_units, status,

-- NEW (+7)
basement_floors INTEGER DEFAULT 0,      -- Number of basement floors
stilt_floors INTEGER DEFAULT 0,         -- Number of stilt floors
podium_floors INTEGER DEFAULT 0,        -- Number of podium floors
height_meters NUMERIC(6,2),             -- Building height in meters
plan_approval_number VARCHAR(100),      -- Approved plan reference
parking_slots_open INTEGER DEFAULT 0,   -- Open parking spaces
parking_slots_covered INTEGER DEFAULT 0 -- Covered parking spaces
```

---

## Table: `land_parcels`

### Before (6 columns)
```sql
id, project_id, survey_number, area_sqmt, owner_name, encumbrance_details
```

### After (10 columns)
```sql
-- Original (6)
id, project_id, survey_number, area_sqmt, owner_name, encumbrance_details,

-- NEW (+4)
ward_number VARCHAR(50),      -- Municipal ward number
mutation_number VARCHAR(100), -- Land mutation number
patwari_halka VARCHAR(100),   -- Patwari circle/halka
plot_number VARCHAR(100)      -- Plot/Khasra number
```

---

## Table: `bank_accounts`

### Before (7 columns)
```sql
id, project_id, bank_name, branch_name, account_number, ifsc_code, account_holder_name
```

### After (11 columns)
```sql
-- Original (7)
id, project_id, bank_name, branch_name, account_number, ifsc_code, account_holder_name,

-- NEW (+4)
account_type VARCHAR(50),            -- Type of account (escrow, etc.)
authorized_signatories TEXT,         -- Account signatories
total_funds_received NUMERIC(18,2),  -- Total deposits
total_funds_utilized NUMERIC(18,2)   -- Total withdrawals
```

---

## Table: `quarterly_updates`

### Before (7 columns)
```sql
id, project_id, quarter, update_date, status, summary, raw_data_json
```

### After (13 columns)
```sql
-- Original (7)
id, project_id, quarter, update_date, status, summary, raw_data_json,

-- NEW (+6)
foundation_percent NUMERIC(5,2),     -- Foundation completion %
plinth_percent NUMERIC(5,2),         -- Plinth completion %
superstructure_percent NUMERIC(5,2), -- Structure completion %
mep_percent NUMERIC(5,2),            -- MEP (electrical/plumbing) %
finishing_percent NUMERIC(5,2),      -- Internal finishing %
overall_percent NUMERIC(5,2)         -- Overall project completion %
```

---

## Table: `project_unit_types`

### Before (existing columns)
```sql
id, project_id, unit_label, unit_type, bedroom_count,
carpet_area_min_sqft, carpet_area_max_sqft,
super_builtup_area_min_sqft, super_builtup_area_max_sqft,
...
```

### After (+ 6 columns)
```sql
-- NEW columns
balcony_area_sqft NUMERIC(10,2),      -- Balcony area
common_area_sqft NUMERIC(10,2),       -- Common area allocation
terrace_area_sqft NUMERIC(10,2),      -- Exclusive terrace area
open_parking_price NUMERIC(12,2),     -- Open parking cost
covered_parking_price NUMERIC(12,2),  -- Covered parking cost
club_membership_fee NUMERIC(12,2)     -- Club membership fee
```

---

## Table: `project_artifacts`

### Before
```sql
id, project_id, category, artifact_type, file_path, source_url, ...
```

### After (+ 1 column)
```sql
-- NEW column
document_type_id INTEGER  -- FK to document_types lookup
```

---

## NEW Table: `localities`

```sql
CREATE TABLE localities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(128) NOT NULL UNIQUE,
    district VARCHAR(128),
    state_code VARCHAR(10),
    lat NUMERIC(9,6),
    lon NUMERIC(9,6),
    pincode VARCHAR(10),
    locality_type VARCHAR(50),      -- 'village', 'ward', 'colony', 'sector'
    parent_locality_id INTEGER REFERENCES localities(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_localities_district ON localities(district);
CREATE INDEX ix_localities_pincode ON localities(pincode);
```

---

## NEW Table: `document_types`

```sql
CREATE TABLE document_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),       -- 'legal', 'technical', 'approvals', 'media'
    is_required BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0
);
```

### Seed Data
| code | name | category | is_required |
|------|------|----------|-------------|
| registration_certificate | Registration Certificate | legal | TRUE |
| building_plan | Building Plan | technical | TRUE |
| layout_plan | Layout Plan | technical | TRUE |
| fire_noc | Fire NOC | approvals | FALSE |
| environment_noc | Environment NOC | approvals | FALSE |
| airport_noc | Airport NOC | approvals | FALSE |
| encumbrance_certificate | Encumbrance Certificate | legal | FALSE |
| commencement_certificate | Commencement Certificate | approvals | FALSE |
| occupancy_certificate | Occupancy Certificate | approvals | FALSE |
| completion_certificate | Completion Certificate | approvals | FALSE |
| site_photo | Site Photo | media | FALSE |
| project_brochure | Project Brochure | media | FALSE |
| revenue_document | Revenue Document | legal | FALSE |
| land_title_deed | Land Title Deed | legal | FALSE |

---

## Dropped Tables

| Table | Reason |
|-------|--------|
| `testabc` | Test table, not needed |

---

## Column Statistics Summary

| Table | Before | After | Added |
|-------|--------|-------|-------|
| projects | 32 | 42 | +10 |
| promoters | 8 | 10 | +2 |
| buildings | 7 | 14 | +7 |
| land_parcels | 6 | 10 | +4 |
| bank_accounts | 7 | 11 | +4 |
| quarterly_updates | 7 | 13 | +6 |
| project_unit_types | ~20 | ~26 | +6 |
| project_artifacts | ~10 | ~11 | +1 |
| localities | 0 | 12 | NEW |
| document_types | 0 | 6 | NEW |
| **TOTAL** | ~97 | ~145 | **+48** |
