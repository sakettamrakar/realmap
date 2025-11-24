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
            ALTER TABLE amenity_poi
                ADD COLUMN IF NOT EXISTS search_radius_km NUMERIC(4, 2);
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


MIGRATIONS: list[tuple[str, MigrationFunc]] = [
    ("20250305_add_geo_columns", _add_geo_columns),
    ("20250322_create_amenity_tables", _create_amenity_tables),
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
