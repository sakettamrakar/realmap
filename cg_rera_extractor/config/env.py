"""Helpers for configuring database-related environment variables."""
from __future__ import annotations

import os
from urllib.parse import urlsplit

DEFAULT_DATABASE_URL = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"


def ensure_database_url() -> str:
    """Ensure ``DATABASE_URL`` is set and return its value.

    If the environment variable is missing we fall back to the canonical Postgres
    instance provided for this project.
    """

    url = os.getenv("DATABASE_URL")
    if url:
        return url

    os.environ["DATABASE_URL"] = DEFAULT_DATABASE_URL
    return DEFAULT_DATABASE_URL


def describe_database_target(url: str | None = None) -> str:
    """Return a sanitized ``host/database`` description for logging."""

    active_url = url or os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL
    # Handle SQLAlchemy URL objects
    if hasattr(active_url, 'render_as_string'):
        active_url = active_url.render_as_string(hide_password=True)
    elif not isinstance(active_url, str):
        active_url = str(active_url)
    parts = urlsplit(active_url)
    host = parts.hostname or "unknown-host"
    database = parts.path.lstrip("/") or "<default>"
    return f"{host}/{database}"


__all__ = ["DEFAULT_DATABASE_URL", "describe_database_target", "ensure_database_url"]
