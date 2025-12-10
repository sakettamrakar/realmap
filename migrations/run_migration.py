"""Run database migration script."""
from sqlalchemy import text
from cg_rera_extractor.db import get_engine

def run_migration():
    """Execute the data audit schema migration."""
    engine = get_engine()
    
    # Define migration statements individually (avoiding DO $$ blocks for simplicity)
    statements = [
        # Phase 1.1: Projects table
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_website_url VARCHAR(1024)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS number_of_phases INTEGER DEFAULT 1",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS fsi_approved NUMERIC(6,2)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS far_approved NUMERIC(6,2)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS has_litigation BOOLEAN DEFAULT FALSE",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS open_space_area_sqmt NUMERIC(14,2)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS approved_building_coverage NUMERIC(6,2)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS total_complaints INTEGER DEFAULT 0",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS complaints_resolved INTEGER DEFAULT 0",
        "CREATE INDEX IF NOT EXISTS ix_projects_has_litigation ON projects(has_litigation)",
        
        # Phase 1.2: Promoters table
        "ALTER TABLE promoters ADD COLUMN IF NOT EXISTS gst_number VARCHAR(20)",
        "ALTER TABLE promoters ADD COLUMN IF NOT EXISTS authorized_signatory VARCHAR(255)",
        
        # Phase 1.3: Land parcels table
        "ALTER TABLE land_parcels ADD COLUMN IF NOT EXISTS ward_number VARCHAR(50)",
        "ALTER TABLE land_parcels ADD COLUMN IF NOT EXISTS mutation_number VARCHAR(100)",
        "ALTER TABLE land_parcels ADD COLUMN IF NOT EXISTS patwari_halka VARCHAR(100)",
        "ALTER TABLE land_parcels ADD COLUMN IF NOT EXISTS plot_number VARCHAR(100)",
        
        # Phase 1.4: Buildings table
        "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS basement_floors INTEGER DEFAULT 0",
        "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS stilt_floors INTEGER DEFAULT 0",
        "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS podium_floors INTEGER DEFAULT 0",
        "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS height_meters NUMERIC(6,2)",
        "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS plan_approval_number VARCHAR(100)",
        "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS parking_slots_open INTEGER DEFAULT 0",
        "ALTER TABLE buildings ADD COLUMN IF NOT EXISTS parking_slots_covered INTEGER DEFAULT 0",
        
        # Phase 2.1: Project unit types
        "ALTER TABLE project_unit_types ADD COLUMN IF NOT EXISTS balcony_area_sqft NUMERIC(10,2)",
        "ALTER TABLE project_unit_types ADD COLUMN IF NOT EXISTS common_area_sqft NUMERIC(10,2)",
        "ALTER TABLE project_unit_types ADD COLUMN IF NOT EXISTS terrace_area_sqft NUMERIC(10,2)",
        "ALTER TABLE project_unit_types ADD COLUMN IF NOT EXISTS open_parking_price NUMERIC(12,2)",
        "ALTER TABLE project_unit_types ADD COLUMN IF NOT EXISTS covered_parking_price NUMERIC(12,2)",
        "ALTER TABLE project_unit_types ADD COLUMN IF NOT EXISTS club_membership_fee NUMERIC(12,2)",
        
        # Phase 2.2: Bank accounts table
        "ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS account_type VARCHAR(50)",
        "ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS authorized_signatories TEXT",
        "ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS total_funds_received NUMERIC(18,2)",
        "ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS total_funds_utilized NUMERIC(18,2)",
        
        # Phase 2.3: Quarterly updates table
        "ALTER TABLE quarterly_updates ADD COLUMN IF NOT EXISTS foundation_percent NUMERIC(5,2)",
        "ALTER TABLE quarterly_updates ADD COLUMN IF NOT EXISTS plinth_percent NUMERIC(5,2)",
        "ALTER TABLE quarterly_updates ADD COLUMN IF NOT EXISTS superstructure_percent NUMERIC(5,2)",
        "ALTER TABLE quarterly_updates ADD COLUMN IF NOT EXISTS mep_percent NUMERIC(5,2)",
        "ALTER TABLE quarterly_updates ADD COLUMN IF NOT EXISTS finishing_percent NUMERIC(5,2)",
        "ALTER TABLE quarterly_updates ADD COLUMN IF NOT EXISTS overall_percent NUMERIC(5,2)",
        
        # Phase 3.1: Localities table
        """CREATE TABLE IF NOT EXISTS localities (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(128) NOT NULL UNIQUE,
            district VARCHAR(128),
            state_code VARCHAR(10),
            lat NUMERIC(9,6),
            lon NUMERIC(9,6),
            pincode VARCHAR(10),
            locality_type VARCHAR(50),
            parent_locality_id INTEGER REFERENCES localities(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )""",
        "CREATE INDEX IF NOT EXISTS ix_localities_district ON localities(district)",
        "CREATE INDEX IF NOT EXISTS ix_localities_pincode ON localities(pincode)",
        
        # Phase 3.2: Link projects to localities
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS locality_id INTEGER",
        "CREATE INDEX IF NOT EXISTS ix_projects_locality_id ON projects(locality_id)",
        
        # Phase 3.3: Document types table
        """CREATE TABLE IF NOT EXISTS document_types (
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            is_required BOOLEAN DEFAULT FALSE,
            display_order INTEGER DEFAULT 0
        )""",
        
        # Phase 3.4: Link artifacts to document types
        "ALTER TABLE project_artifacts ADD COLUMN IF NOT EXISTS document_type_id INTEGER",
        
        # Data migration for deprecated fields
        """UPDATE projects 
        SET geo_source = COALESCE(geo_source, geocoding_source)
        WHERE geo_source IS NULL AND geocoding_source IS NOT NULL""",
        """UPDATE projects 
        SET geo_formatted_address = COALESCE(geo_formatted_address, formatted_address)
        WHERE geo_formatted_address IS NULL AND formatted_address IS NOT NULL""",
        
        # Cleanup test table
        "DROP TABLE IF EXISTS testabc",
    ]
    
    # Seed document types
    seed_document_types = """
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
    ON CONFLICT (code) DO NOTHING
    """
    
    with engine.connect() as conn:
        success_count = 0
        error_count = 0
        
        for stmt in statements:
            try:
                conn.execute(text(stmt))
                success_count += 1
                # Print short summary
                print(f"✓ {stmt[:50]}...")
            except Exception as e:
                error_count += 1
                print(f"✗ {stmt[:50]}... Error: {str(e)[:50]}")
        
        # Seed document types
        try:
            conn.execute(text(seed_document_types))
            print("✓ Seeded document_types")
            success_count += 1
        except Exception as e:
            print(f"✗ Seeding document_types: {e}")
            error_count += 1
        
        conn.commit()
        print("\n=== Migration Complete ===")
        print(f"Success: {success_count}")
        print(f"Errors: {error_count}")


if __name__ == "__main__":
    run_migration()
