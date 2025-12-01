"""Lightweight, idempotent schema migrations."""
from __future__ import annotations

from typing import Callable, Iterable

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

MigrationFunc = Callable[[Connection], None]


def _add_geo_columns(conn: Connection) -> None:
    """Add GEO-related columns to the projects table."""

    conn.execute(
        text(
            """
            ALTER TABLE projects
                ADD COLUMN IF NOT EXISTS geo_precision VARCHAR(32),
                ADD COLUMN IF NOT EXISTS geo_confidence NUMERIC(4, 3),
                ADD COLUMN IF NOT EXISTS geo_source VARCHAR(128),
                ADD COLUMN IF NOT EXISTS geo_normalized_address VARCHAR(512),
                ADD COLUMN IF NOT EXISTS geo_formatted_address VARCHAR(512);
            """
        )
    )


def _create_amenity_tables(conn: Connection) -> None:
    """Create amenity and scoring tables if they do not exist."""

    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS amenity_poi (
                id SERIAL PRIMARY KEY,
                provider VARCHAR(64) NOT NULL,
                provider_place_id VARCHAR(255) NOT NULL,
                amenity_type VARCHAR(64) NOT NULL,
                name VARCHAR(255),
                lat NUMERIC(9, 6) NOT NULL,
                lon NUMERIC(9, 6) NOT NULL,
                formatted_address VARCHAR(1024),
                source_raw JSONB,
                last_seen_at TIMESTAMPTZ,
                search_radius_km NUMERIC(4, 2),
                created_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ,
                UNIQUE (provider, provider_place_id)
            );

            CREATE INDEX IF NOT EXISTS ix_amenity_poi_type_lat_lon
                ON amenity_poi (amenity_type, lat, lon);
            """
        )
    )

    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS project_amenity_stats (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                amenity_type VARCHAR(64) NOT NULL,
                radius_km NUMERIC(4, 2) NOT NULL,
                count_within_radius INTEGER,
                nearest_distance_km NUMERIC(6, 3),
                provider_snapshot VARCHAR(128),
                last_computed_at TIMESTAMPTZ,
                UNIQUE (project_id, amenity_type, radius_km)
            );

            CREATE INDEX IF NOT EXISTS ix_project_amenity_stats_project_id
                ON project_amenity_stats (project_id);
            CREATE INDEX IF NOT EXISTS ix_project_amenity_stats_amenity_type
                ON project_amenity_stats (amenity_type);
            """
        )
    )

    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS project_scores (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                connectivity_score INTEGER,
                daily_needs_score INTEGER,
                social_infra_score INTEGER,
                overall_score INTEGER,
                score_version VARCHAR(32),
                last_computed_at TIMESTAMPTZ,
                UNIQUE (project_id)
            );

            CREATE INDEX IF NOT EXISTS ix_project_scores_project_id
                ON project_scores (project_id);
            """
        )
    )



def _create_project_locations_table(conn: Connection) -> None:
    """Create project_locations table."""
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS project_locations (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                source_type VARCHAR(64) NOT NULL,
                lat NUMERIC(9, 6) NOT NULL,
                lon NUMERIC(9, 6) NOT NULL,
                precision_level VARCHAR(32),
                confidence_score NUMERIC(4, 3),
                is_active BOOLEAN DEFAULT TRUE,
                meta_data JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ
            );

            CREATE INDEX IF NOT EXISTS ix_project_locations_project_id
                ON project_locations (project_id);
            CREATE INDEX IF NOT EXISTS ix_project_locations_source_type
                ON project_locations (source_type);
            """
        )
    )



def _update_amenity_schema(conn: Connection) -> None:
    """Update schema for onsite vs nearby separation."""
    conn.execute(
        text(
            """
            -- Update project_amenity_stats
            ALTER TABLE project_amenity_stats
                ALTER COLUMN radius_km DROP NOT NULL,
                ADD COLUMN IF NOT EXISTS nearby_count INTEGER,
                ADD COLUMN IF NOT EXISTS nearby_nearest_km NUMERIC(6, 3),
                ADD COLUMN IF NOT EXISTS onsite_available BOOLEAN,
                ADD COLUMN IF NOT EXISTS onsite_details JSONB;
            
            -- Rename old columns to new ones if data exists (optional, or just drop/ignore)
            -- For now we keep old columns or map them if needed, but let's assume we recompute.
            -- We can drop old columns if we want to be clean, but let's keep it additive for safety.
            
            -- Update project_scores
            ALTER TABLE project_scores
                ADD COLUMN IF NOT EXISTS amenity_score INTEGER,
                ADD COLUMN IF NOT EXISTS location_score INTEGER;
            """
        )
    )


def _create_phase6_read_model(conn: Connection) -> None:
    """Indexes and view to support Phase 6 search/map queries."""

    conn.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_projects_district
                ON projects (district);
            CREATE INDEX IF NOT EXISTS ix_projects_tehsil
                ON projects (tehsil);
            CREATE INDEX IF NOT EXISTS ix_projects_status
                ON projects (status);
            CREATE INDEX IF NOT EXISTS ix_projects_registration_date
                ON projects (approved_date);

            CREATE INDEX IF NOT EXISTS ix_project_scores_overall_score
                ON project_scores (overall_score);
            CREATE INDEX IF NOT EXISTS ix_project_scores_location_score
                ON project_scores (location_score);
            CREATE INDEX IF NOT EXISTS ix_project_scores_amenity_score
                ON project_scores (amenity_score);

            CREATE INDEX IF NOT EXISTS ix_project_locations_active_lat_lon
                ON project_locations (lat, lon)
                WHERE is_active;

            CREATE INDEX IF NOT EXISTS ix_project_amenity_stats_project_radius
                ON project_amenity_stats (project_id, radius_km);
            """
        )
    )

    conn.execute(text("DROP VIEW IF EXISTS project_search_view"))

    conn.execute(
        text(
            """
            CREATE OR REPLACE VIEW project_search_view AS
            WITH canonical_location AS (
                SELECT
                    pl.project_id,
                    pl.lat,
                    pl.lon,
                    pl.source_type,
                    pl.precision_level,
                    pl.confidence_score,
                    pl.updated_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY pl.project_id
                        ORDER BY COALESCE(pl.confidence_score, 0) DESC, pl.updated_at DESC NULLS LAST, pl.id DESC
                    ) AS rn
                FROM project_locations pl
                WHERE pl.is_active IS TRUE
            ),
            amenity_rollup AS (
                SELECT DISTINCT ON (pas.project_id)
                    pas.project_id,
                    pas.onsite_available,
                    pas.onsite_details
                FROM project_amenity_stats pas
                WHERE pas.radius_km IS NULL
                ORDER BY pas.project_id, pas.id DESC
            ),
            nearby_rollup AS (
                SELECT
                    pas.project_id,
                    SUM(COALESCE(pas.nearby_count, 0)) AS total_nearby_count,
                    MIN(pas.nearby_nearest_km) AS nearest_nearby_km
                FROM project_amenity_stats pas
                WHERE pas.radius_km IS NOT NULL
                GROUP BY pas.project_id
            )
            SELECT
                p.id AS project_id,
                p.state_code,
                p.rera_registration_number,
                p.project_name,
                p.status,
                p.district,
                p.tehsil,
                p.village_or_locality,
                p.full_address,
                COALESCE(cl.lat, p.latitude) AS lat,
                COALESCE(cl.lon, p.longitude) AS lon,
                COALESCE(cl.source_type, p.geo_source) AS geo_source,
                COALESCE(cl.precision_level, p.geo_precision) AS geo_precision,
                COALESCE(cl.confidence_score, p.geo_confidence) AS geo_confidence,
                p.approved_date AS registration_date,
                p.proposed_end_date,
                p.extended_end_date,
                ps.overall_score,
                ps.location_score,
                ps.amenity_score,
                ps.score_version,
                ar.onsite_available,
                ar.onsite_details,
                nr.total_nearby_count,
                nr.nearest_nearby_km
            FROM projects p
            LEFT JOIN canonical_location cl
                ON cl.project_id = p.id AND cl.rn = 1
            LEFT JOIN project_scores ps
                ON ps.project_id = p.id
            LEFT JOIN amenity_rollup ar
                ON ar.project_id = p.id
            LEFT JOIN nearby_rollup nr
                ON nr.project_id = p.id;
            """
        )
    )


def _add_score_status_columns(conn: Connection) -> None:
    """Add score status columns, update types, and refresh search view."""
    
    # 0. Drop view first because it depends on columns we are about to change
    conn.execute(text("DROP VIEW IF EXISTS project_search_view"))

    # 1. Add new columns
    conn.execute(
        text(
            """
            ALTER TABLE project_scores
                ADD COLUMN IF NOT EXISTS score_status VARCHAR(32),
                ADD COLUMN IF NOT EXISTS score_status_reason JSONB,
                ADD COLUMN IF NOT EXISTS value_score NUMERIC(5, 2);
            """
        )
    )

    # 2. Update score column types to NUMERIC(5, 2)
    # Note: We cast existing values to numeric.
    conn.execute(
        text(
            """
            ALTER TABLE project_scores
                ALTER COLUMN amenity_score TYPE NUMERIC(5, 2) USING amenity_score::numeric,
                ALTER COLUMN location_score TYPE NUMERIC(5, 2) USING location_score::numeric,
                ALTER COLUMN overall_score TYPE NUMERIC(5, 2) USING overall_score::numeric;
            """
        )
    )

    # 3. Add index on score_status
    conn.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_project_scores_score_status
                ON project_scores (score_status);
            """
        )
    )

    # 4. Update the view to include new columns
    conn.execute(
        text(
            """
            CREATE OR REPLACE VIEW project_search_view AS
            WITH canonical_location AS (
                SELECT
                    pl.project_id,
                    pl.lat,
                    pl.lon,
                    pl.source_type,
                    pl.precision_level,
                    pl.confidence_score,
                    pl.updated_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY pl.project_id
                        ORDER BY COALESCE(pl.confidence_score, 0) DESC, pl.updated_at DESC NULLS LAST, pl.id DESC
                    ) AS rn
                FROM project_locations pl
                WHERE pl.is_active IS TRUE
            ),
            amenity_rollup AS (
                SELECT DISTINCT ON (pas.project_id)
                    pas.project_id,
                    pas.onsite_available,
                    pas.onsite_details
                FROM project_amenity_stats pas
                    WHERE pas.radius_km IS NULL
                ORDER BY pas.project_id, pas.id DESC
            ),
            nearby_rollup AS (
                SELECT
                    pas.project_id,
                    SUM(COALESCE(pas.nearby_count, 0)) AS total_nearby_count,
                    MIN(pas.nearby_nearest_km) AS nearest_nearby_km
                FROM project_amenity_stats pas
                WHERE pas.radius_km IS NOT NULL
                GROUP BY pas.project_id
            )
            SELECT
                p.id AS project_id,
                p.state_code,
                p.rera_registration_number,
                p.project_name,
                p.status,
                p.district,
                p.tehsil,
                p.village_or_locality,
                p.full_address,
                COALESCE(cl.lat, p.latitude) AS lat,
                COALESCE(cl.lon, p.longitude) AS lon,
                COALESCE(cl.source_type, p.geo_source) AS geo_source,
                COALESCE(cl.precision_level, p.geo_precision) AS geo_precision,
                COALESCE(cl.confidence_score, p.geo_confidence) AS geo_confidence,
                p.approved_date AS registration_date,
                p.proposed_end_date,
                p.extended_end_date,
                ps.overall_score,
                ps.location_score,
                ps.amenity_score,
                ps.score_status,
                ps.score_status_reason,
                ps.score_version,
                ar.onsite_available,
                ar.onsite_details,
                nr.total_nearby_count,
                nr.nearest_nearby_km
            FROM projects p
            LEFT JOIN canonical_location cl
                ON cl.project_id = p.id AND cl.rn = 1
            LEFT JOIN project_scores ps
                ON ps.project_id = p.id
            LEFT JOIN amenity_rollup ar
                ON ar.project_id = p.id
            LEFT JOIN nearby_rollup nr
                ON nr.project_id = p.id;
            """
        )
    )


def _create_price_tables(conn: Connection) -> None:
    """Create tables for unit types and pricing snapshots."""
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS project_unit_types (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                unit_label VARCHAR(100),
                bedrooms INTEGER,
                bathrooms INTEGER,
                carpet_area_min_sqft NUMERIC(10, 2),
                carpet_area_max_sqft NUMERIC(10, 2),
                super_builtup_area_min_sqft NUMERIC(10, 2),
                super_builtup_area_max_sqft NUMERIC(10, 2),
                is_active BOOLEAN DEFAULT TRUE,
                raw_data JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ
            );

            CREATE INDEX IF NOT EXISTS ix_project_unit_types_project_id
                ON project_unit_types (project_id);

            CREATE TABLE IF NOT EXISTS project_pricing_snapshots (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                snapshot_date DATE NOT NULL,
                unit_type_label VARCHAR(100),
                min_price_total NUMERIC(14, 2),
                max_price_total NUMERIC(14, 2),
                min_price_per_sqft NUMERIC(10, 2),
                max_price_per_sqft NUMERIC(10, 2),
                source_type VARCHAR(50),
                source_reference VARCHAR(1024),
                raw_data JSONB,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS ix_project_pricing_snapshots_project_date
                ON project_pricing_snapshots (project_id, snapshot_date);
            CREATE INDEX IF NOT EXISTS ix_project_pricing_snapshots_min_price
                ON project_pricing_snapshots (min_price_total);
            CREATE INDEX IF NOT EXISTS ix_project_pricing_snapshots_max_price
                ON project_pricing_snapshots (max_price_total);
            """
        )
    )


def _update_view_with_prices(conn: Connection) -> None:
    """Update project_search_view to include latest price info."""
    
    conn.execute(text("DROP VIEW IF EXISTS project_search_view"))

    conn.execute(
        text(
            """
            CREATE OR REPLACE VIEW project_search_view AS
            WITH canonical_location AS (
                SELECT
                    pl.project_id,
                    pl.lat,
                    pl.lon,
                    pl.source_type,
                    pl.precision_level,
                    pl.confidence_score,
                    pl.updated_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY pl.project_id
                        ORDER BY COALESCE(pl.confidence_score, 0) DESC, pl.updated_at DESC NULLS LAST, pl.id DESC
                    ) AS rn
                FROM project_locations pl
                WHERE pl.is_active IS TRUE
            ),
            amenity_rollup AS (
                SELECT DISTINCT ON (pas.project_id)
                    pas.project_id,
                    pas.onsite_available,
                    pas.onsite_details
                FROM project_amenity_stats pas
                    WHERE pas.radius_km IS NULL
                ORDER BY pas.project_id, pas.id DESC
            ),
            nearby_rollup AS (
                SELECT
                    pas.project_id,
                    SUM(COALESCE(pas.nearby_count, 0)) AS total_nearby_count,
                    MIN(pas.nearby_nearest_km) AS nearest_nearby_km
                FROM project_amenity_stats pas
                WHERE pas.radius_km IS NOT NULL
                GROUP BY pas.project_id
            ),
            latest_prices AS (
                SELECT DISTINCT ON (pps.project_id)
                    pps.project_id,
                    pps.min_price_total,
                    pps.max_price_total,
                    pps.min_price_per_sqft,
                    pps.max_price_per_sqft
                FROM project_pricing_snapshots pps
                WHERE pps.is_active IS TRUE
                ORDER BY pps.project_id, pps.snapshot_date DESC, pps.id DESC
            )
            SELECT
                p.id AS project_id,
                p.state_code,
                p.rera_registration_number,
                p.project_name,
                p.status,
                p.district,
                p.tehsil,
                p.village_or_locality,
                p.full_address,
                COALESCE(cl.lat, p.latitude) AS lat,
                COALESCE(cl.lon, p.longitude) AS lon,
                COALESCE(cl.source_type, p.geo_source) AS geo_source,
                COALESCE(cl.precision_level, p.geo_precision) AS geo_precision,
                COALESCE(cl.confidence_score, p.geo_confidence) AS geo_confidence,
                p.approved_date AS registration_date,
                p.proposed_end_date,
                p.extended_end_date,
                ps.overall_score,
                ps.location_score,
                ps.amenity_score,
                ps.score_status,
                ps.score_status_reason,
                ps.score_version,
                ar.onsite_available,
                ar.onsite_details,
                nr.total_nearby_count,
                nr.nearest_nearby_km,
                lp.min_price_total,
                lp.max_price_total,
                lp.min_price_per_sqft,
                lp.max_price_per_sqft
            FROM projects p
            LEFT JOIN canonical_location cl
                ON cl.project_id = p.id AND cl.rn = 1
            LEFT JOIN project_scores ps
                ON ps.project_id = p.id
            LEFT JOIN amenity_rollup ar
                ON ar.project_id = p.id
            LEFT JOIN nearby_rollup nr
                ON nr.project_id = p.id
            LEFT JOIN latest_prices lp
                ON lp.project_id = p.id;
            """
        )
    )


def _create_discovery_tables(conn: Connection) -> None:
    """Create tables for Discovery & Trust Layer (Points 24-26)."""
    
    # ==========================================================================
    # Point 24: Tags for Faceted Search
    # ==========================================================================
    conn.execute(
        text(
            """
            -- Create tag_category enum type
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tag_category') THEN
                    CREATE TYPE tag_category AS ENUM (
                        'PROXIMITY',
                        'INFRASTRUCTURE', 
                        'INVESTMENT',
                        'LIFESTYLE',
                        'CERTIFICATION'
                    );
                END IF;
            END$$;

            -- Create tags table
            CREATE TABLE IF NOT EXISTS tags (
                id SERIAL PRIMARY KEY,
                slug VARCHAR(100) NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                category tag_category NOT NULL,
                is_auto_generated BOOLEAN DEFAULT FALSE,
                auto_rule_json JSONB,
                icon_emoji VARCHAR(10),
                color_hex VARCHAR(7),
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                is_featured BOOLEAN DEFAULT FALSE,
                seo_title VARCHAR(255),
                seo_description VARCHAR(500),
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ,
                CONSTRAINT uq_tags_slug UNIQUE (slug)
            );

            CREATE INDEX IF NOT EXISTS ix_tags_category ON tags (category);
            CREATE INDEX IF NOT EXISTS ix_tags_is_active ON tags (is_active);
            CREATE INDEX IF NOT EXISTS ix_tags_is_featured ON tags (is_featured);

            -- Create project_tags join table
            CREATE TABLE IF NOT EXISTS project_tags (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
                is_auto_applied BOOLEAN DEFAULT FALSE,
                confidence_score NUMERIC(4, 3),
                applied_by VARCHAR(100),
                applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                computed_distance_km NUMERIC(6, 2),
                CONSTRAINT uq_project_tag UNIQUE (project_id, tag_id)
            );

            CREATE INDEX IF NOT EXISTS ix_project_tags_project_id ON project_tags (project_id);
            CREATE INDEX IF NOT EXISTS ix_project_tags_tag_id ON project_tags (tag_id);
            """
        )
    )

    # ==========================================================================
    # Point 25: RERA Verification System
    # ==========================================================================
    conn.execute(
        text(
            """
            -- Create rera_verification_status enum type
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'rera_verification_status') THEN
                    CREATE TYPE rera_verification_status AS ENUM (
                        'VERIFIED',
                        'PENDING',
                        'REVOKED',
                        'EXPIRED',
                        'NOT_FOUND',
                        'UNKNOWN'
                    );
                END IF;
            END$$;

            -- Create rera_verifications table
            CREATE TABLE IF NOT EXISTS rera_verifications (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                status rera_verification_status NOT NULL DEFAULT 'UNKNOWN',
                official_record_url VARCHAR(1024),
                portal_screenshot_url VARCHAR(1024),
                registered_name_on_portal VARCHAR(500),
                promoter_name_on_portal VARCHAR(500),
                portal_registration_date TIMESTAMPTZ,
                portal_expiry_date TIMESTAMPTZ,
                verified_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                verified_by VARCHAR(100),
                verification_method VARCHAR(50),
                has_discrepancies BOOLEAN DEFAULT FALSE,
                discrepancy_notes TEXT,
                raw_portal_data JSONB,
                is_current BOOLEAN DEFAULT TRUE
            );

            CREATE INDEX IF NOT EXISTS ix_rera_verifications_project_id ON rera_verifications (project_id);
            CREATE INDEX IF NOT EXISTS ix_rera_verifications_status ON rera_verifications (status);
            CREATE INDEX IF NOT EXISTS ix_rera_verifications_is_current ON rera_verifications (is_current);
            """
        )
    )

    # ==========================================================================
    # Point 26: Landmarks & Entity Linking
    # ==========================================================================
    conn.execute(
        text(
            """
            -- Create landmarks table
            CREATE TABLE IF NOT EXISTS landmarks (
                id SERIAL PRIMARY KEY,
                slug VARCHAR(100) NOT NULL,
                name VARCHAR(255) NOT NULL,
                alternate_names JSONB,
                category VARCHAR(50) NOT NULL,
                subcategory VARCHAR(50),
                lat NUMERIC(9, 6) NOT NULL,
                lon NUMERIC(9, 6) NOT NULL,
                address VARCHAR(512),
                city VARCHAR(128),
                district VARCHAR(128),
                state VARCHAR(128),
                established_year INTEGER,
                website VARCHAR(500),
                image_url VARCHAR(1024),
                description TEXT,
                importance_score INTEGER DEFAULT 50,
                default_proximity_km NUMERIC(4, 1) DEFAULT 5.0,
                seo_title VARCHAR(255),
                seo_description VARCHAR(500),
                is_active BOOLEAN DEFAULT TRUE,
                is_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ,
                CONSTRAINT uq_landmarks_slug UNIQUE (slug)
            );

            CREATE INDEX IF NOT EXISTS ix_landmarks_category ON landmarks (category);
            CREATE INDEX IF NOT EXISTS ix_landmarks_lat_lon ON landmarks (lat, lon);
            CREATE INDEX IF NOT EXISTS ix_landmarks_city ON landmarks (city);
            CREATE INDEX IF NOT EXISTS ix_landmarks_is_active ON landmarks (is_active);

            -- Create project_landmarks join table
            CREATE TABLE IF NOT EXISTS project_landmarks (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                landmark_id INTEGER NOT NULL REFERENCES landmarks(id) ON DELETE CASCADE,
                distance_km NUMERIC(6, 2) NOT NULL,
                driving_time_mins INTEGER,
                walking_time_mins INTEGER,
                is_highlighted BOOLEAN DEFAULT FALSE,
                display_order INTEGER DEFAULT 0,
                calculated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_project_landmark UNIQUE (project_id, landmark_id)
            );

            CREATE INDEX IF NOT EXISTS ix_project_landmarks_project_id ON project_landmarks (project_id);
            CREATE INDEX IF NOT EXISTS ix_project_landmarks_landmark_id ON project_landmarks (landmark_id);
            CREATE INDEX IF NOT EXISTS ix_project_landmarks_distance ON project_landmarks (distance_km);
            """
        )
    )


def _update_view_with_discovery(conn: Connection) -> None:
    """Update project_search_view to include RERA verification status and tag count."""
    
    conn.execute(text("DROP VIEW IF EXISTS project_search_view"))

    conn.execute(
        text(
            """
            CREATE OR REPLACE VIEW project_search_view AS
            WITH canonical_location AS (
                SELECT
                    pl.project_id,
                    pl.lat,
                    pl.lon,
                    pl.source_type,
                    pl.precision_level,
                    pl.confidence_score,
                    pl.updated_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY pl.project_id
                        ORDER BY COALESCE(pl.confidence_score, 0) DESC, pl.updated_at DESC NULLS LAST, pl.id DESC
                    ) AS rn
                FROM project_locations pl
                WHERE pl.is_active IS TRUE
            ),
            amenity_rollup AS (
                SELECT DISTINCT ON (pas.project_id)
                    pas.project_id,
                    pas.onsite_available,
                    pas.onsite_details
                FROM project_amenity_stats pas
                    WHERE pas.radius_km IS NULL
                ORDER BY pas.project_id, pas.id DESC
            ),
            nearby_rollup AS (
                SELECT
                    pas.project_id,
                    SUM(COALESCE(pas.nearby_count, 0)) AS total_nearby_count,
                    MIN(pas.nearby_nearest_km) AS nearest_nearby_km
                FROM project_amenity_stats pas
                WHERE pas.radius_km IS NOT NULL
                GROUP BY pas.project_id
            ),
            latest_prices AS (
                SELECT DISTINCT ON (pps.project_id)
                    pps.project_id,
                    pps.min_price_total,
                    pps.max_price_total,
                    pps.min_price_per_sqft,
                    pps.max_price_per_sqft
                FROM project_pricing_snapshots pps
                WHERE pps.is_active IS TRUE
                ORDER BY pps.project_id, pps.snapshot_date DESC, pps.id DESC
            ),
            rera_status AS (
                SELECT DISTINCT ON (rv.project_id)
                    rv.project_id,
                    rv.status AS rera_verification_status,
                    rv.verified_at AS rera_verified_at,
                    rv.has_discrepancies AS rera_has_discrepancies
                FROM rera_verifications rv
                WHERE rv.is_current IS TRUE
                ORDER BY rv.project_id, rv.verified_at DESC
            ),
            tag_counts AS (
                SELECT
                    pt.project_id,
                    COUNT(*) AS tag_count,
                    ARRAY_AGG(t.slug ORDER BY t.sort_order) AS tag_slugs
                FROM project_tags pt
                JOIN tags t ON t.id = pt.tag_id
                WHERE t.is_active IS TRUE
                GROUP BY pt.project_id
            )
            SELECT
                p.id AS project_id,
                p.state_code,
                p.rera_registration_number,
                p.project_name,
                p.status,
                p.district,
                p.tehsil,
                p.village_or_locality,
                p.full_address,
                COALESCE(cl.lat, p.latitude) AS lat,
                COALESCE(cl.lon, p.longitude) AS lon,
                COALESCE(cl.source_type, p.geo_source) AS geo_source,
                COALESCE(cl.precision_level, p.geo_precision) AS geo_precision,
                COALESCE(cl.confidence_score, p.geo_confidence) AS geo_confidence,
                p.approved_date AS registration_date,
                p.proposed_end_date,
                p.extended_end_date,
                ps.overall_score,
                ps.location_score,
                ps.amenity_score,
                ps.score_status,
                ps.score_status_reason,
                ps.score_version,
                ar.onsite_available,
                ar.onsite_details,
                nr.total_nearby_count,
                nr.nearest_nearby_km,
                lp.min_price_total,
                lp.max_price_total,
                lp.min_price_per_sqft,
                lp.max_price_per_sqft,
                -- Discovery columns (Points 24-26)
                rs.rera_verification_status,
                rs.rera_verified_at,
                rs.rera_has_discrepancies,
                tc.tag_count,
                tc.tag_slugs
            FROM projects p
            LEFT JOIN canonical_location cl
                ON cl.project_id = p.id AND cl.rn = 1
            LEFT JOIN project_scores ps
                ON ps.project_id = p.id
            LEFT JOIN amenity_rollup ar
                ON ar.project_id = p.id
            LEFT JOIN nearby_rollup nr
                ON nr.project_id = p.id
            LEFT JOIN latest_prices lp
                ON lp.project_id = p.id
            LEFT JOIN rera_status rs
                ON rs.project_id = p.id
            LEFT JOIN tag_counts tc
                ON tc.project_id = p.id;
            """
        )
    )


def _add_qa_columns(conn: Connection) -> None:
    """Add QA and Ops columns to projects table."""
    conn.execute(
        text(
            """
            ALTER TABLE projects
                ADD COLUMN IF NOT EXISTS qa_flags JSONB,
                ADD COLUMN IF NOT EXISTS qa_status VARCHAR(32),
                ADD COLUMN IF NOT EXISTS qa_last_checked_at TIMESTAMPTZ;
            """
        )
    )


def _add_granular_scores(conn: Connection) -> None:
    """Add granular score columns to project_scores."""
    print("Running _add_granular_scores migration...")
    conn.execute(
        text(
            """
            ALTER TABLE project_scores
                ADD COLUMN IF NOT EXISTS lifestyle_score NUMERIC(4, 2),
                ADD COLUMN IF NOT EXISTS safety_score NUMERIC(4, 2),
                ADD COLUMN IF NOT EXISTS environment_score NUMERIC(4, 2),
                ADD COLUMN IF NOT EXISTS investment_potential_score NUMERIC(4, 2),
                ADD COLUMN IF NOT EXISTS structured_ratings JSONB;
            """
        )
    )


def _add_granular_price_and_unit_columns(conn: Connection) -> None:
    """Add granular price and unit columns."""
    print("Running _add_granular_price_and_unit_columns migration...")
    conn.execute(
        text(
            """
            ALTER TABLE project_pricing_snapshots
                ADD COLUMN IF NOT EXISTS price_per_sqft_carpet_min NUMERIC(10, 2),
                ADD COLUMN IF NOT EXISTS price_per_sqft_carpet_max NUMERIC(10, 2),
                ADD COLUMN IF NOT EXISTS price_per_sqft_sbua_min NUMERIC(10, 2),
                ADD COLUMN IF NOT EXISTS price_per_sqft_sbua_max NUMERIC(10, 2);
                
            ALTER TABLE project_unit_types
                ADD COLUMN IF NOT EXISTS balcony_count INTEGER,
                ADD COLUMN IF NOT EXISTS builtup_area_min_sqft NUMERIC(10, 2),
                ADD COLUMN IF NOT EXISTS builtup_area_max_sqft NUMERIC(10, 2),
                ADD COLUMN IF NOT EXISTS canonical_area_unit VARCHAR(10) DEFAULT 'SQFT',
                ADD COLUMN IF NOT EXISTS maintenance_fee_monthly NUMERIC(10, 2),
                ADD COLUMN IF NOT EXISTS maintenance_fee_per_sqft NUMERIC(8, 2);
            """
        )
    )


MIGRATIONS: list[tuple[str, MigrationFunc]] = [
    ("20250305_add_geo_columns", _add_geo_columns),
    ("20250322_create_amenity_tables", _create_amenity_tables),
    ("20250401_create_project_locations", _create_project_locations_table),
    ("20250415_separate_amenity_scopes", _update_amenity_schema),
    ("20250428_phase6_read_model", _create_phase6_read_model),
    ("20250510_add_score_status", _add_score_status_columns),
    ("20250525_create_price_tables", _create_price_tables),
    ("20250526_update_view_with_prices", _update_view_with_prices),
    ("20250601_create_discovery_tables", _create_discovery_tables),
    ("20250602_update_view_with_discovery", _update_view_with_discovery),
    ("20250615_add_qa_columns", _add_qa_columns),
    ("20250620_add_granular_scores", _add_granular_scores),
    ("20250625_add_granular_price_and_unit_columns", _add_granular_price_and_unit_columns),
]


def apply_migrations(engine: Engine, *, migrations: Iterable[tuple[str, MigrationFunc]] | None = None) -> list[str]:
    """Apply all known migrations."""

    applied: list[str] = []
    to_run = list(migrations) if migrations is not None else MIGRATIONS

    with engine.begin() as conn:
        for name, migration in to_run:
            migration(conn)
            applied.append(name)

    return applied


__all__ = ["apply_migrations", "MIGRATIONS"]
