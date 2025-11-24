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


MIGRATIONS: list[tuple[str, MigrationFunc]] = [
    ("20250305_add_geo_columns", _add_geo_columns),
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
