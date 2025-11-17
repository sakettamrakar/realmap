"""Dependencies used by the FastAPI application."""
from __future__ import annotations

import logging
from collections.abc import Iterator

from sqlalchemy.orm import Session

from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
from cg_rera_extractor.db.base import get_engine, get_session_local

LOGGER = logging.getLogger(__name__)

# Global session factory backed by the configured database URL.
ensure_database_url()
_engine = get_engine()
LOGGER.info("API session factory configured for %s", describe_database_target())
SessionLocal = get_session_local(_engine)


def get_db() -> Iterator[Session]:
    """Yield a database session for request-scoped usage."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["get_db", "SessionLocal"]
