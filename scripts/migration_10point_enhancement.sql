-- =============================================================================
-- 10-Point Enhancement Standard - Database Migration
-- =============================================================================
-- 
-- This migration adds new tables and columns to support the enhanced data model.
-- Run this migration AFTER backing up your database.
--
-- Enhancement Reference:
-- #1: Developer Identity (Entity Promotion)
-- #2: Hierarchy Restructuring (Project > Tower > Unit)
-- #3: Explicit Area Normalization
-- #4: Price Per Sqft by Area Type
-- #5: Structured Possession Timelines
-- #7: Amenities Taxonomy
-- #8: Inventory Variants (Unit Types) - Enhanced
-- #9: Transaction Registry
-- #10: Granular Ratings System
-- =============================================================================

-- =============================================================================
-- Enhancement #1: Developer Identity (Entity Promotion)
-- =============================================================================

CREATE TABLE IF NOT EXISTS developers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    state_code VARCHAR(10),
    legal_name VARCHAR(500),
    estd_year INTEGER,
    trust_score NUMERIC(4, 2),
    total_delivered_sqft NUMERIC(14, 2),
    total_projects_completed INTEGER,
    total_projects_ongoing INTEGER,
    headquarters_city VARCHAR(128),
    website VARCHAR(500),
    logo_url VARCHAR(1024),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uq_developer_name_state UNIQUE (name, state_code)
);

CREATE INDEX IF NOT EXISTS ix_developers_trust_score ON developers(trust_score);

CREATE TABLE IF NOT EXISTS developer_projects (
    id SERIAL PRIMARY KEY,
    developer_id INTEGER NOT NULL REFERENCES developers(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role VARCHAR(50),
    ownership_percentage NUMERIC(5, 2),
    CONSTRAINT uq_developer_project UNIQUE (developer_id, project_id)
);

-- =============================================================================
-- Enhancement #2: Hierarchy Restructuring (Unit Entity)
-- =============================================================================

CREATE TABLE IF NOT EXISTS units (
    id SERIAL PRIMARY KEY,
    building_id INTEGER NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    unit_type_id INTEGER REFERENCES project_unit_types(id) ON DELETE SET NULL,
    unit_number VARCHAR(50) NOT NULL,
    floor_number INTEGER,
    wing VARCHAR(20),
    carpet_area_sqft NUMERIC(10, 2),
    builtup_area_sqft NUMERIC(10, 2),
    super_builtup_area_sqft NUMERIC(10, 2),
    status VARCHAR(30) DEFAULT 'AVAILABLE',
    is_corner_unit BOOLEAN,
    facing_direction VARCHAR(20),
    base_price NUMERIC(14, 2),
    price_per_sqft_carpet NUMERIC(10, 2),
    price_per_sqft_sbua NUMERIC(10, 2),
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uq_building_unit_number UNIQUE (building_id, unit_number)
);

CREATE INDEX IF NOT EXISTS ix_units_building_id ON units(building_id);
CREATE INDEX IF NOT EXISTS ix_units_status ON units(status);
CREATE INDEX IF NOT EXISTS ix_units_floor ON units(floor_number);

-- =============================================================================
-- Enhancement #3: Explicit Area Normalization
-- Add missing area columns to project_unit_types
-- =============================================================================

ALTER TABLE project_unit_types 
    ADD COLUMN IF NOT EXISTS builtup_area_min_sqft NUMERIC(10, 2),
    ADD COLUMN IF NOT EXISTS builtup_area_max_sqft NUMERIC(10, 2),
    ADD COLUMN IF NOT EXISTS canonical_area_unit VARCHAR(10) DEFAULT 'SQFT';

-- =============================================================================
-- Enhancement #4: Price Per Sqft by Area Type
-- Add area-specific pricing to pricing snapshots
-- =============================================================================

ALTER TABLE project_pricing_snapshots 
    ADD COLUMN IF NOT EXISTS price_per_sqft_carpet_min NUMERIC(10, 2),
    ADD COLUMN IF NOT EXISTS price_per_sqft_carpet_max NUMERIC(10, 2),
    ADD COLUMN IF NOT EXISTS price_per_sqft_sbua_min NUMERIC(10, 2),
    ADD COLUMN IF NOT EXISTS price_per_sqft_sbua_max NUMERIC(10, 2);

-- =============================================================================
-- Enhancement #5: Structured Possession Timelines
-- =============================================================================

CREATE TABLE IF NOT EXISTS project_possession_timelines (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    building_id INTEGER REFERENCES buildings(id) ON DELETE CASCADE,
    marketing_target DATE,
    regulatory_deadline DATE,
    rera_deadline DATE,
    actual_completion DATE,
    phase VARCHAR(30) DEFAULT 'UNDER_CONSTRUCTION',
    phase_start_date DATE,
    delay_months INTEGER,
    delay_reason VARCHAR(500),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_possession_timelines_project_id ON project_possession_timelines(project_id);
CREATE INDEX IF NOT EXISTS ix_possession_timelines_phase ON project_possession_timelines(phase);

-- =============================================================================
-- Enhancement #7: Amenities Taxonomy
-- =============================================================================

CREATE TABLE IF NOT EXISTS amenity_categories (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    icon VARCHAR(50),
    display_order INTEGER DEFAULT 0,
    lifestyle_weight NUMERIC(4, 2),
    CONSTRAINT uq_amenity_category_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS amenities (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES amenity_categories(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    icon VARCHAR(50),
    lifestyle_points INTEGER,
    CONSTRAINT uq_amenity_code UNIQUE (code)
);

CREATE INDEX IF NOT EXISTS ix_amenities_category_id ON amenities(category_id);

CREATE TABLE IF NOT EXISTS amenity_types (
    id SERIAL PRIMARY KEY,
    amenity_id INTEGER NOT NULL REFERENCES amenities(id) ON DELETE CASCADE,
    variant_code VARCHAR(50) NOT NULL,
    variant_name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    premium_multiplier NUMERIC(3, 2) DEFAULT 1.0,
    CONSTRAINT uq_amenity_variant UNIQUE (amenity_id, variant_code)
);

CREATE TABLE IF NOT EXISTS project_amenities (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    amenity_type_id INTEGER NOT NULL REFERENCES amenity_types(id) ON DELETE CASCADE,
    is_available BOOLEAN DEFAULT TRUE,
    is_chargeable BOOLEAN,
    monthly_fee NUMERIC(10, 2),
    quantity INTEGER DEFAULT 1,
    size_sqft NUMERIC(10, 2),
    details VARCHAR(500),
    images JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_project_amenity_type UNIQUE (project_id, amenity_type_id)
);

CREATE INDEX IF NOT EXISTS ix_project_amenities_project_id ON project_amenities(project_id);

-- =============================================================================
-- Enhancement #8: Inventory Variants (Unit Types) - Enhanced
-- Add balcony_count and maintenance fields
-- =============================================================================

ALTER TABLE project_unit_types 
    ADD COLUMN IF NOT EXISTS balcony_count INTEGER,
    ADD COLUMN IF NOT EXISTS maintenance_fee_monthly NUMERIC(10, 2),
    ADD COLUMN IF NOT EXISTS maintenance_fee_per_sqft NUMERIC(8, 2);

-- =============================================================================
-- Enhancement #9: Transaction Registry
-- =============================================================================

CREATE TABLE IF NOT EXISTS transaction_history (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    building_id INTEGER REFERENCES buildings(id) ON DELETE SET NULL,
    unit_id INTEGER REFERENCES units(id) ON DELETE SET NULL,
    registry_date DATE,
    registry_number VARCHAR(100),
    sub_registrar_office VARCHAR(255),
    declared_amount NUMERIC(14, 2),
    stamp_duty_paid NUMERIC(12, 2),
    registration_fee NUMERIC(12, 2),
    registered_area_sqft NUMERIC(10, 2),
    area_type VARCHAR(20),
    price_per_sqft_registered NUMERIC(10, 2),
    anonymized_buyer_hash VARCHAR(64),
    buyer_type VARCHAR(30),
    source_type VARCHAR(50),
    source_reference VARCHAR(500),
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    verified_at TIMESTAMP WITH TIME ZONE,
    verification_status VARCHAR(30)
);

CREATE INDEX IF NOT EXISTS ix_transactions_project_id ON transaction_history(project_id);
CREATE INDEX IF NOT EXISTS ix_transactions_registry_date ON transaction_history(registry_date);
CREATE INDEX IF NOT EXISTS ix_transactions_price_sqft ON transaction_history(price_per_sqft_registered);

-- =============================================================================
-- Enhancement #10: Granular Ratings System
-- Add new rating columns to project_scores
-- =============================================================================

ALTER TABLE project_scores 
    ADD COLUMN IF NOT EXISTS lifestyle_score NUMERIC(4, 2),
    ADD COLUMN IF NOT EXISTS safety_score NUMERIC(4, 2),
    ADD COLUMN IF NOT EXISTS environment_score NUMERIC(4, 2),
    ADD COLUMN IF NOT EXISTS investment_potential_score NUMERIC(4, 2),
    ADD COLUMN IF NOT EXISTS structured_ratings JSONB;

-- =============================================================================
-- Seed Data: Amenity Taxonomy (Enhancement #7)
-- =============================================================================

-- Insert amenity categories
INSERT INTO amenity_categories (code, name, description, icon, display_order, lifestyle_weight)
VALUES 
    ('HEALTH', 'Health & Fitness', 'Gym, pool, sports facilities', 'heart', 1, 8.0),
    ('LEISURE', 'Leisure & Recreation', 'Clubhouse, party hall, games', 'gamepad', 2, 7.0),
    ('CONVENIENCE', 'Convenience', 'Parking, power backup, water', 'shopping-cart', 3, 6.0),
    ('CONNECTIVITY', 'Connectivity', 'EV charging, internet, intercom', 'wifi', 4, 5.0),
    ('SECURITY', 'Security', 'CCTV, guards, access control', 'shield', 5, 9.0),
    ('ENVIRONMENT', 'Environment', 'Gardens, parks, green spaces', 'tree', 6, 7.5),
    ('SOCIAL', 'Social Infrastructure', 'Schools, hospitals nearby', 'users', 7, 8.5)
ON CONFLICT (code) DO NOTHING;

-- Insert common amenities
INSERT INTO amenities (category_id, code, name, description, lifestyle_points)
SELECT c.id, a.code, a.name, a.description, a.points
FROM amenity_categories c
CROSS JOIN (VALUES
    ('HEALTH', 'swimming_pool', 'Swimming Pool', 'Shared swimming facility', 8),
    ('HEALTH', 'gym', 'Gymnasium', 'Fitness center with equipment', 7),
    ('HEALTH', 'yoga_room', 'Yoga Room', 'Dedicated yoga/meditation space', 5),
    ('HEALTH', 'sports_court', 'Sports Court', 'Tennis/basketball court', 6),
    ('LEISURE', 'clubhouse', 'Clubhouse', 'Community clubhouse', 7),
    ('LEISURE', 'party_hall', 'Party Hall', 'Banquet/party area', 5),
    ('LEISURE', 'childrens_play', 'Children Play Area', 'Kids playground', 6),
    ('CONVENIENCE', 'covered_parking', 'Covered Parking', 'Covered car parking', 4),
    ('CONVENIENCE', 'power_backup', 'Power Backup', '24/7 power backup', 5),
    ('CONVENIENCE', 'water_supply', '24/7 Water Supply', 'Continuous water supply', 5),
    ('CONNECTIVITY', 'ev_charging', 'EV Charging', 'Electric vehicle charging', 4),
    ('CONNECTIVITY', 'high_speed_internet', 'High Speed Internet', 'Fiber connectivity', 3),
    ('SECURITY', 'cctv', 'CCTV Surveillance', '24/7 CCTV monitoring', 6),
    ('SECURITY', 'gated_community', 'Gated Community', 'Secured gated entry', 7),
    ('SECURITY', 'security_guards', 'Security Guards', '24/7 security personnel', 6),
    ('ENVIRONMENT', 'landscaped_garden', 'Landscaped Garden', 'Maintained gardens', 6),
    ('ENVIRONMENT', 'jogging_track', 'Jogging Track', 'Walking/jogging path', 5),
    ('ENVIRONMENT', 'rainwater_harvesting', 'Rainwater Harvesting', 'Water conservation', 4)
) AS a(cat_code, code, name, description, points)
WHERE c.code = a.cat_code
ON CONFLICT (code) DO NOTHING;

-- Insert amenity types (variants)
INSERT INTO amenity_types (amenity_id, variant_code, variant_name, description, premium_multiplier)
SELECT a.id, t.variant_code, t.variant_name, t.description, t.multiplier
FROM amenities a
CROSS JOIN (VALUES
    ('swimming_pool', 'indoor', 'Indoor Pool', 'Temperature controlled indoor pool', 1.5),
    ('swimming_pool', 'outdoor', 'Outdoor Pool', 'Open air swimming pool', 1.0),
    ('swimming_pool', 'infinity', 'Infinity Pool', 'Luxury infinity edge pool', 2.0),
    ('gym', 'basic', 'Basic Gym', 'Standard fitness equipment', 1.0),
    ('gym', 'premium', 'Premium Gym', 'High-end equipment with trainers', 1.5),
    ('covered_parking', 'single', 'Single Parking', 'One covered parking slot', 1.0),
    ('covered_parking', 'stacked', 'Stacked Parking', 'Mechanical stacked parking', 0.8),
    ('clubhouse', 'standard', 'Standard Clubhouse', 'Basic community facilities', 1.0),
    ('clubhouse', 'premium', 'Premium Clubhouse', 'Luxury clubhouse with multiple facilities', 1.5)
) AS t(amenity_code, variant_code, variant_name, description, multiplier)
WHERE a.code = t.amenity_code
ON CONFLICT (amenity_id, variant_code) DO NOTHING;

-- =============================================================================
-- Migration for flat unit data (Enhancement #2)
-- Creates default "Tower A" building and migrates units if needed
-- =============================================================================

-- This is a TEMPLATE for migrating flat unit data
-- Uncomment and customize based on your actual data structure

-- INSERT INTO buildings (project_id, building_name, building_type, status)
-- SELECT DISTINCT p.id, 'Tower A', 'Residential Tower', 'Active'
-- FROM projects p
-- WHERE NOT EXISTS (SELECT 1 FROM buildings b WHERE b.project_id = p.id)
-- AND EXISTS (SELECT 1 FROM unit_types ut WHERE ut.project_id = p.id);

-- =============================================================================
-- Refresh views and statistics
-- =============================================================================

-- ANALYZE developers;
-- ANALYZE units;
-- ANALYZE transaction_history;
-- ANALYZE project_possession_timelines;
-- ANALYZE amenity_categories;
-- ANALYZE amenities;
-- ANALYZE amenity_types;
-- ANALYZE project_amenities;

COMMENT ON TABLE developers IS 'Enhancement #1: First-class Developer entity with track record';
COMMENT ON TABLE units IS 'Enhancement #2: Individual unit inventory within towers';
COMMENT ON TABLE transaction_history IS 'Enhancement #9: Registry transaction records';
COMMENT ON TABLE project_possession_timelines IS 'Enhancement #5: Structured possession dates';
COMMENT ON TABLE amenity_categories IS 'Enhancement #7: Amenity taxonomy - categories';
COMMENT ON TABLE amenities IS 'Enhancement #7: Amenity taxonomy - amenities';
COMMENT ON TABLE amenity_types IS 'Enhancement #7: Amenity taxonomy - variants';
COMMENT ON TABLE project_amenities IS 'Enhancement #7: Project-amenity linkage';
