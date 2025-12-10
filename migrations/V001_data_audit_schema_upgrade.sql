-- Migration: V001_data_audit_schema_upgrade.sql
-- Description: Schema upgrades based on data audit findings
-- Date: 2024-12-10
-- Phase: 1-3 (Critical fixes, Area/Pricing, Normalization)

-- ============================================================================
-- PHASE 1.1: Add Missing Extracted Fields to `projects`
-- ============================================================================

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
CREATE INDEX IF NOT EXISTS ix_projects_number_of_phases ON projects(number_of_phases);

-- ============================================================================
-- PHASE 1.2: Add Missing Fields to `promoters`
-- ============================================================================

ALTER TABLE promoters
    ADD COLUMN IF NOT EXISTS gst_number VARCHAR(20),
    ADD COLUMN IF NOT EXISTS authorized_signatory VARCHAR(255);

-- ============================================================================
-- PHASE 1.3: Add Missing Fields to `land_parcels`
-- ============================================================================

ALTER TABLE land_parcels
    ADD COLUMN IF NOT EXISTS ward_number VARCHAR(50),
    ADD COLUMN IF NOT EXISTS mutation_number VARCHAR(100),
    ADD COLUMN IF NOT EXISTS patwari_halka VARCHAR(100),
    ADD COLUMN IF NOT EXISTS plot_number VARCHAR(100);

-- ============================================================================
-- PHASE 1.4: Add Missing Fields to `buildings`
-- ============================================================================

ALTER TABLE buildings
    ADD COLUMN IF NOT EXISTS basement_floors INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS stilt_floors INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS podium_floors INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS height_meters NUMERIC(6,2),
    ADD COLUMN IF NOT EXISTS plan_approval_number VARCHAR(100),
    ADD COLUMN IF NOT EXISTS parking_slots_open INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS parking_slots_covered INTEGER DEFAULT 0;

-- ============================================================================
-- PHASE 2.1: Add Additional Unit Area Breakdowns
-- ============================================================================

ALTER TABLE project_unit_types
    ADD COLUMN IF NOT EXISTS balcony_area_sqft NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS common_area_sqft NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS terrace_area_sqft NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS open_parking_price NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS covered_parking_price NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS club_membership_fee NUMERIC(12,2);

-- ============================================================================
-- PHASE 2.2: Add Missing Bank Account Fields
-- ============================================================================

ALTER TABLE bank_accounts
    ADD COLUMN IF NOT EXISTS account_type VARCHAR(50),
    ADD COLUMN IF NOT EXISTS authorized_signatories TEXT,
    ADD COLUMN IF NOT EXISTS total_funds_received NUMERIC(18,2),
    ADD COLUMN IF NOT EXISTS total_funds_utilized NUMERIC(18,2);

-- ============================================================================
-- PHASE 2.3: Enhance Quarterly Updates for Progress Tracking
-- ============================================================================

ALTER TABLE quarterly_updates
    ADD COLUMN IF NOT EXISTS foundation_percent NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS plinth_percent NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS superstructure_percent NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS mep_percent NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS finishing_percent NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS overall_percent NUMERIC(5,2);

-- ============================================================================
-- PHASE 3.1: Create Locality Taxonomy
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS ix_localities_district ON localities(district);
CREATE INDEX IF NOT EXISTS ix_localities_pincode ON localities(pincode);
CREATE INDEX IF NOT EXISTS ix_localities_state_code ON localities(state_code);

-- ============================================================================
-- PHASE 3.2: Link Projects to Localities
-- ============================================================================

ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS locality_id INTEGER REFERENCES localities(id);

CREATE INDEX IF NOT EXISTS ix_projects_locality_id ON projects(locality_id);

-- ============================================================================
-- PHASE 3.3: Create Document Type Lookup
-- ============================================================================

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
    ('occupancy_certificate', 'Occupancy Certificate', 'approvals', FALSE, 9),
    ('completion_certificate', 'Completion Certificate', 'approvals', FALSE, 10),
    ('site_photo', 'Site Photo', 'media', FALSE, 11),
    ('project_brochure', 'Project Brochure', 'media', FALSE, 12),
    ('revenue_document', 'Revenue Document', 'legal', FALSE, 13),
    ('land_title_deed', 'Land Title Deed', 'legal', FALSE, 14)
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- PHASE 3.4: Normalize project_artifacts with Document Types
-- ============================================================================

ALTER TABLE project_artifacts
    ADD COLUMN IF NOT EXISTS document_type_id INTEGER REFERENCES document_types(id);

CREATE INDEX IF NOT EXISTS ix_project_artifacts_document_type ON project_artifacts(document_type_id);

-- ============================================================================
-- PHASE 4.1: Seed Amenity Categories (if table exists)
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'amenity_categories') THEN
        INSERT INTO amenity_categories (code, name, description, lifestyle_weight, display_order) VALUES
            ('health_fitness', 'Health & Fitness', 'Gym, swimming pool, sports facilities', 2.0, 1),
            ('leisure', 'Leisure & Entertainment', 'Clubhouse, party hall, gaming', 1.5, 2),
            ('security', 'Security', 'CCTV, gated entry, security staff', 2.5, 3),
            ('green_space', 'Green Spaces', 'Garden, park, landscaping', 1.5, 4),
            ('convenience', 'Convenience', 'Power backup, water supply, parking', 2.0, 5),
            ('community', 'Community', 'Community hall, temple, common areas', 1.0, 6)
        ON CONFLICT (code) DO NOTHING;
    END IF;
END $$;

-- ============================================================================
-- PHASE 4.2: Seed Common Amenities (if table exists)
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'amenities') THEN
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
            ('health_fitness', 'yoga_room', 'Yoga Room', 4),
            ('health_fitness', 'sports_court', 'Sports Court', 6),
            ('leisure', 'clubhouse', 'Clubhouse', 7),
            ('leisure', 'indoor_games', 'Indoor Games Room', 5),
            ('leisure', 'party_hall', 'Party Hall', 4),
            ('leisure', 'mini_theatre', 'Mini Theatre', 6),
            ('security', 'cctv', 'CCTV Surveillance', 6),
            ('security', 'gated_entry', 'Gated Entry', 8),
            ('security', 'security_guards', '24x7 Security', 8),
            ('security', 'intercom', 'Intercom System', 5),
            ('green_space', 'garden', 'Landscaped Garden', 6),
            ('green_space', 'children_play', 'Children Play Area', 7),
            ('green_space', 'senior_citizen_area', 'Senior Citizen Area', 4),
            ('convenience', 'power_backup', 'Power Backup', 9),
            ('convenience', 'water_supply', '24x7 Water Supply', 8),
            ('convenience', 'car_parking', 'Car Parking', 6),
            ('convenience', 'lift', 'Elevator/Lift', 7),
            ('convenience', 'rainwater_harvesting', 'Rainwater Harvesting', 5),
            ('community', 'community_hall', 'Community Hall', 4),
            ('community', 'temple', 'Temple/Prayer Hall', 3),
            ('community', 'multipurpose_room', 'Multipurpose Room', 4)
        ) AS a(cat_code, code, name, points)
        WHERE c.code = a.cat_code
        ON CONFLICT (code) DO NOTHING;
    END IF;
END $$;

-- ============================================================================
-- PHASE 5: Data Migration for Deprecated Fields
-- ============================================================================

-- Migrate geocoding_source to geo_source
UPDATE projects 
SET geo_source = COALESCE(geo_source, geocoding_source)
WHERE geo_source IS NULL AND geocoding_source IS NOT NULL;

-- Migrate formatted_address to geo_formatted_address
UPDATE projects 
SET geo_formatted_address = COALESCE(geo_formatted_address, formatted_address)
WHERE geo_formatted_address IS NULL AND formatted_address IS NOT NULL;

-- ============================================================================
-- CLEANUP: Remove test table
-- ============================================================================

DROP TABLE IF EXISTS testabc;

-- ============================================================================
-- VERIFICATION: Print migration completion message
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration V001_data_audit_schema_upgrade completed successfully';
END $$;
