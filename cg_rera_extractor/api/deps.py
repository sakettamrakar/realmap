"""Dependencies used by the FastAPI application."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from cg_rera_extractor.db.base import get_engine, get_session_local

# Global session factory backed by the configured database URL.
_engine = get_engine()
SessionLocal = get_session_local(_engine)


def get_db() -> Iterator[Session]:
    """Yield a database session for request-scoped usage."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["get_db", "SessionLocal"]
