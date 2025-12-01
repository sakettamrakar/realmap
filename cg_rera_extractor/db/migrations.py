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


MIGRATIONS: list[tuple[str, MigrationFunc]] = [
    ("20250305_add_geo_columns", _add_geo_columns),
    ("20250322_create_amenity_tables", _create_amenity_tables),
    ("20250401_create_project_locations", _create_project_locations_table),
    ("20250415_separate_amenity_scopes", _update_amenity_schema),
    ("20250428_phase6_read_model", _create_phase6_read_model),
    ("20250510_add_score_status", _add_score_status_columns),
    ("20250525_create_price_tables", _create_price_tables),
    ("20250526_update_view_with_prices", _update_view_with_prices),
]


def apply_migrations(engine: Engine, *, migrations: Iterable[tuple[str, MigrationFunc]] | None = None) -> list[str]:
    """Apply all known migrations.

    Each migration is expected to be idempotent (using ``IF NOT EXISTS``) so that
    the runner can be safely re-executed. Returns the ordered list of migration
    identifiers that were invoked.
    """

    applied: list[str] = []
    to_run = list(migrations) if migrations is not None else MIGRATIONS

    with engine.begin() as conn:
        for name, migration in to_run:
            migration(conn)
            applied.append(name)

    return applied


__all__ = ["apply_migrations", "MIGRATIONS"]
