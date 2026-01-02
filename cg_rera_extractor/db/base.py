"""Database base classes and connection helpers."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# SQLAlchemy 1.4/2.0 compatibility for Base class
try:
    # SQLAlchemy 2.0+
    from sqlalchemy.orm import DeclarativeBase
    
    class Base(DeclarativeBase):
        """Declarative base for all ORM models (SQLAlchemy 2.0 style).
        
        Note: __allow_unmapped__ = True is required for compatibility with
        Apache Airflow's model scanner when using SQLAlchemy 2.0 Mapped[] annotations.
        """
        __allow_unmapped__ = True
        
except ImportError:
    # SQLAlchemy 1.4.x fallback
    from sqlalchemy.orm import declarative_base
    
    Base = declarative_base()
    # Add attribute for compatibility
    Base.__allow_unmapped__ = True

from cg_rera_extractor.config.env import ensure_database_url
from cg_rera_extractor.config.models import DatabaseConfig


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

    database_url = url or (database_config.url if database_config else None)
    if not database_url:
        database_url = ensure_database_url()

    return create_engine(database_url, echo=echo, future=True)


def get_session_local(engine: Engine) -> sessionmaker[Session]:
    """Return a sessionmaker factory bound to the provided engine."""

    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


__all__ = ["Base", "get_engine", "get_session_local"]
