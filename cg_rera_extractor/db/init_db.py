"""Schema initialization helpers."""
from __future__ import annotations

from sqlalchemy.engine import Engine

from .base import Base, get_engine

# Import models so that Base.metadata is populated before create_all is invoked.
# pylint: disable=unused-import
from . import models  # noqa: F401


def init_db(engine: Engine | None = None) -> None:
    """Create all tables if they do not exist."""

    resolved_engine = engine or get_engine()
    Base.metadata.create_all(resolved_engine)
