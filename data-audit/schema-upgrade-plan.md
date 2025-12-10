# Schema Upgrade Plan

> **Audit Date**: December 10, 2024  
> **Target Version**: v2.0  
> **Implementation Timeline**: 4-6 weeks

---

## Overview

This document proposes schema enhancements based on the data audit findings. Changes are categorized by impact level and include SQL migration templates.

---

## Phase 1: Critical Fixes (Week 1-2)

### 1.1 Add Missing Extracted Fields to `projects`

```sql
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS project_website_url VARCHAR(1024),
    ADD COLUMN IF NOT EXISTS number_of_phases INTEGER DEFAULT 1,
    ADD COLUMN IF NOT EXISTS fsi_approved NUMERIC(6,2),
    ADD COLUMN IF NOT EXISTS far_approved NUMERIC(6,2),
    ADD COLUMN IF NOT EXISTS has_litigation BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS open_space_area_sqmt NUMERIC(14,2),
    ADD COLUMN IF NOT EXISTS approved_building_coverage NUMERIC(6,2),
    ADD COLUMN IF NOT EXISTS total_complaints INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS complaints_resolved INTEGER DEFAULT 0;

-- Add index for filtering
CREATE INDEX IF NOT EXISTS ix_projects_has_litigation ON projects(has_litigation);
```

### 1.2 Add Missing Fields to `promoters`

```sql
ALTER TABLE promoters
    ADD COLUMN IF NOT EXISTS gst_number VARCHAR(20),
    ADD COLUMN IF NOT EXISTS authorized_signatory VARCHAR(255);
```

### 1.3 Add Missing Fields to `land_parcels`

```sql
ALTER TABLE land_parcels
    ADD COLUMN IF NOT EXISTS ward_number VARCHAR(50),
    ADD COLUMN IF NOT EXISTS mutation_number VARCHAR(100),
    ADD COLUMN IF NOT EXISTS patwari_halka VARCHAR(100),
    ADD COLUMN IF NOT EXISTS plot_number VARCHAR(100);
```

### 1.4 Add Missing Fields to `buildings`

```sql
ALTER TABLE buildings
    ADD COLUMN IF NOT EXISTS basement_floors INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS stilt_floors INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS podium_floors INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS height_meters NUMERIC(6,2),
    ADD COLUMN IF NOT EXISTS plan_approval_number VARCHAR(100),
    ADD COLUMN IF NOT EXISTS parking_slots_open INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS parking_slots_covered INTEGER DEFAULT 0;
```

---

## Phase 2: Area & Pricing Normalization (Week 2-3)

### 2.1 Add SQFT Columns (Enhancement #3 Completion)

```sql
-- project_unit_types already has sqft columns, ensure they're populated
-- Add additional area breakdowns

ALTER TABLE project_unit_types
    ADD COLUMN IF NOT EXISTS balcony_area_sqft NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS common_area_sqft NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS terrace_area_sqft NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS open_parking_price NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS covered_parking_price NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS club_membership_fee NUMERIC(12,2);
```

### 2.2 Add Missing Bank Account Fields

```sql
ALTER TABLE bank_accounts
    ADD COLUMN IF NOT EXISTS account_type VARCHAR(50),
    ADD COLUMN IF NOT EXISTS authorized_signatories TEXT,
    ADD COLUMN IF NOT EXISTS total_funds_received NUMERIC(18,2),
    ADD COLUMN IF NOT EXISTS total_funds_utilized NUMERIC(18,2);
```

### 2.3 Enhance Quarterly Updates for Progress Tracking

```sql
ALTER TABLE quarterly_updates
    ADD COLUMN IF NOT EXISTS foundation_percent NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS plinth_percent NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS superstructure_percent NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS mep_percent NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS finishing_percent NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS overall_percent NUMERIC(5,2);
```

---

## Phase 3: Normalization & Lookup Tables (Week 3-4)

### 3.1 Create Locality Taxonomy

```sql
CREATE TABLE IF NOT EXISTS localities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(128) NOT NULL UNIQUE,
    district VARCHAR(128),
    state_code VARCHAR(10),
    lat NUMERIC(9,6),
    lon NUMERIC(9,6),
    pincode VARCHAR(10),
    locality_type VARCHAR(50), -- 'village', 'ward', 'colony', 'sector'
    parent_locality_id INTEGER REFERENCES localities(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_localities_district ON localities(district);
CREATE INDEX ix_localities_pincode ON localities(pincode);
```

### 3.2 Link Projects to Localities

```sql
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS locality_id INTEGER REFERENCES localities(id);

CREATE INDEX ix_projects_locality_id ON projects(locality_id);
```

### 3.3 Create Document Type Lookup

```sql
CREATE TABLE IF NOT EXISTS document_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50), -- 'legal', 'technical', 'approvals', 'media'
    is_required BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0
);

-- Seed standard document types
INSERT INTO document_types (code, name, category, is_required, display_order) VALUES
    ('registration_certificate', 'Registration Certificate', 'legal', TRUE, 1),
    ('building_plan', 'Building Plan', 'technical', TRUE, 2),
    ('layout_plan', 'Layout Plan', 'technical', TRUE, 3),
    ('fire_noc', 'Fire NOC', 'approvals', FALSE, 4),
    ('environment_noc', 'Environment NOC', 'approvals', FALSE, 5),
    ('airport_noc', 'Airport NOC', 'approvals', FALSE, 6),
    ('encumbrance_certificate', 'Encumbrance Certificate', 'legal', FALSE, 7),
    ('commencement_certificate', 'Commencement Certificate', 'approvals', FALSE, 8),
    ('occupancy_certificate', 'Occupancy Certificate', 'approvals', FALSE, 9)
ON CONFLICT (code) DO NOTHING;
```

### 3.4 Normalize project_artifacts with Document Types

```sql
ALTER TABLE project_artifacts
    ADD COLUMN IF NOT EXISTS document_type_id INTEGER REFERENCES document_types(id);

CREATE INDEX ix_project_artifacts_document_type ON project_artifacts(document_type_id);
```

---

## Phase 4: Score Computation Infrastructure (Week 4-5)

### 4.1 Seed Amenity Categories

```sql
INSERT INTO amenity_categories (code, name, description, lifestyle_weight, display_order) VALUES
    ('health_fitness', 'Health & Fitness', 'Gym, swimming pool, sports facilities', 2.0, 1),
    ('leisure', 'Leisure & Entertainment', 'Clubhouse, party hall, gaming', 1.5, 2),
    ('security', 'Security', 'CCTV, gated entry, security staff', 2.5, 3),
    ('green_space', 'Green Spaces', 'Garden, park, landscaping', 1.5, 4),
    ('convenience', 'Convenience', 'Power backup, water supply, parking', 2.0, 5),
    ('community', 'Community', 'Community hall, temple, common areas', 1.0, 6)
ON CONFLICT (code) DO NOTHING;
```

### 4.2 Seed Common Amenities

```sql
INSERT INTO amenities (category_id, code, name, lifestyle_points) 
SELECT 
    c.id,
    a.code,
    a.name,
    a.points
FROM amenity_categories c
CROSS JOIN (VALUES
    ('health_fitness', 'gym', 'Gymnasium', 8),
    ('health_fitness', 'swimming_pool', 'Swimming Pool', 10),
    ('health_fitness', 'jogging_track', 'Jogging Track', 5),
    ('leisure', 'clubhouse', 'Clubhouse', 7),
    ('leisure', 'indoor_games', 'Indoor Games Room', 5),
    ('security', 'cctv', 'CCTV Surveillance', 6),
    ('security', 'gated_entry', 'Gated Entry', 8),
    ('security', 'security_guards', '24x7 Security', 8),
    ('green_space', 'garden', 'Landscaped Garden', 6),
    ('green_space', 'children_play', 'Children Play Area', 7),
    ('convenience', 'power_backup', 'Power Backup', 9),
    ('convenience', 'water_supply', '24x7 Water Supply', 8),
    ('convenience', 'car_parking', 'Car Parking', 6),
    ('community', 'community_hall', 'Community Hall', 4),
    ('community', 'temple', 'Temple/Prayer Hall', 3)
) AS a(cat_code, code, name, points)
WHERE c.code = a.cat_code
ON CONFLICT (code) DO NOTHING;
```

---

## Phase 5: Deprecation & Cleanup (Week 5-6)

### 5.1 Columns to Deprecate

| Table | Column | Reason | Action |
|-------|--------|--------|--------|
| `projects` | `geocoding_source` | Replaced by `geo_source` | Keep for 6 months, then drop |
| `projects` | `formatted_address` | Duplicate of `geo_formatted_address` | Merge data, then drop |
| `unit_types` | (entire table) | Replaced by `project_unit_types` | Migrate data, deprecate |
| `project_documents` | (entire table) | Replaced by `project_artifacts` | Already merged |

### 5.2 Migration Script Template

```sql
-- Migrate geocoding_source to geo_source
UPDATE projects 
SET geo_source = COALESCE(geo_source, geocoding_source)
WHERE geo_source IS NULL AND geocoding_source IS NOT NULL;

-- Migrate formatted_address to geo_formatted_address
UPDATE projects 
SET geo_formatted_address = COALESCE(geo_formatted_address, formatted_address)
WHERE geo_formatted_address IS NULL AND formatted_address IS NOT NULL;
```

---

## ORM Model Updates Required

### File: `cg_rera_extractor/db/models.py`

```python
# Add to Project class
project_website_url: Mapped[str | None] = mapped_column(String(1024))
number_of_phases: Mapped[int | None] = mapped_column(Integer, default=1)
fsi_approved: Mapped[Numeric | None] = mapped_column(Numeric(6, 2))
far_approved: Mapped[Numeric | None] = mapped_column(Numeric(6, 2))
has_litigation: Mapped[bool] = mapped_column(Boolean, default=False)
open_space_area_sqmt: Mapped[Numeric | None] = mapped_column(Numeric(14, 2))
approved_building_coverage: Mapped[Numeric | None] = mapped_column(Numeric(6, 2))
total_complaints: Mapped[int | None] = mapped_column(Integer, default=0)
complaints_resolved: Mapped[int | None] = mapped_column(Integer, default=0)
locality_id: Mapped[int | None] = mapped_column(ForeignKey("localities.id"))

# Add to Promoter class
gst_number: Mapped[str | None] = mapped_column(String(20))
authorized_signatory: Mapped[str | None] = mapped_column(String(255))

# Add to Building class
basement_floors: Mapped[int | None] = mapped_column(Integer, default=0)
stilt_floors: Mapped[int | None] = mapped_column(Integer, default=0)
podium_floors: Mapped[int | None] = mapped_column(Integer, default=0)
height_meters: Mapped[Numeric | None] = mapped_column(Numeric(6, 2))
plan_approval_number: Mapped[str | None] = mapped_column(String(100))
parking_slots_open: Mapped[int | None] = mapped_column(Integer, default=0)
parking_slots_covered: Mapped[int | None] = mapped_column(Integer, default=0)
```

---

## Validation Checklist

After each phase, verify:

- [ ] All new columns added to ORM models
- [ ] API schemas updated to expose new fields
- [ ] Frontend types updated in `types/projects.ts`
- [ ] Loader updated to populate new fields
- [ ] Sample data verified in database
- [ ] Tests updated for new schema

---

## Rollback Plan

Each migration should have corresponding rollback:

```sql
-- Example rollback for Phase 1.1
ALTER TABLE projects
    DROP COLUMN IF EXISTS project_website_url,
    DROP COLUMN IF EXISTS number_of_phases,
    DROP COLUMN IF EXISTS fsi_approved,
    DROP COLUMN IF EXISTS far_approved,
    DROP COLUMN IF EXISTS has_litigation,
    DROP COLUMN IF EXISTS open_space_area_sqmt,
    DROP COLUMN IF EXISTS approved_building_coverage,
    DROP COLUMN IF EXISTS total_complaints,
    DROP COLUMN IF EXISTS complaints_resolved;
```
