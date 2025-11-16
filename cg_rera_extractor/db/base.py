"""Database base classes and connection helpers."""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from cg_rera_extractor.config.models import DatabaseConfig


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_engine(
    database_config: DatabaseConfig | None = None,
    *,
    url: str | None = None,
    echo: bool = False,
) -> Engine:
    """Return a SQLAlchemy engine using the provided configuration.

    The URL is resolved in the following precedence order:
    1. Explicit ``url`` argument
    2. ``database_config.url``
    3. ``DATABASE_URL`` environment variable
    """

    database_url = url or (database_config.url if database_config else None) or os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("Database URL must be provided via DatabaseConfig, url argument, or DATABASE_URL env var.")

    return create_engine(database_url, echo=echo, future=True)


def get_session_local(engine: Engine) -> sessionmaker[Session]:
    """Return a sessionmaker factory bound to the provided engine."""

    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


__all__ = ["Base", "get_engine", "get_session_local"]
