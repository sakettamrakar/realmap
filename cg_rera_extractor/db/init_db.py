"""Schema initialization helpers."""
from __future__ import annotations

from sqlalchemy.engine import Engine

from .base import Base, get_engine
from .migrations import apply_migrations

# Import models so that Base.metadata is populated before create_all is invoked.
# pylint: disable=unused-import
from . import models  # noqa: F401
from . import models_discovery  # noqa: F401
from . import models_enhanced  # noqa: F401


def init_db(engine: Engine | None = None, *, run_migrations: bool = True) -> None:
    """Create all tables if they do not exist and run schema migrations."""

    resolved_engine = engine or get_engine()
    Base.metadata.create_all(resolved_engine)
    if run_migrations:
        apply_migrations(resolved_engine)
