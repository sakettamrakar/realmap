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


def _create_amenity_poi(conn: Connection) -> None:
    """Create the amenity_poi cache table."""

    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS amenity_poi (
                id SERIAL PRIMARY KEY,
                provider TEXT NOT NULL,
                provider_place_id TEXT NOT NULL,
                amenity_type TEXT NOT NULL,
                name TEXT,
                lat NUMERIC(9, 6) NOT NULL,
                lon NUMERIC(9, 6) NOT NULL,
                formatted_address TEXT,
                source_raw JSONB,
                last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_amenity_poi_provider_place_id UNIQUE (provider, provider_place_id)
            );
            """
        )
    )


def _add_amenity_search_radius(conn: Connection) -> None:
    """Add search radius column for amenity cache coverage tracking."""

    conn.execute(
        text(
            """
            ALTER TABLE amenity_poi
                ADD COLUMN IF NOT EXISTS search_radius_km NUMERIC(6, 2) DEFAULT 0;
            """
        )
    )


MIGRATIONS: list[tuple[str, MigrationFunc]] = [
    ("20250305_add_geo_columns", _add_geo_columns),
    ("20250515_create_amenity_poi", _create_amenity_poi),
    ("20250520_add_amenity_search_radius", _add_amenity_search_radius),
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
