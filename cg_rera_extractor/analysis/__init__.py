"""Internal analysis utilities for quick project exploration."""
from __future__ import annotations

import logging

from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
from cg_rera_extractor.db.base import get_engine, get_session_local

LOGGER = logging.getLogger(__name__)

# Mirror the API's session factory so analysis helpers share the same config.
ensure_database_url()
_engine = get_engine()
LOGGER.info("Analysis session factory configured for %s", describe_database_target())
SessionLocal = get_session_local(_engine)

__all__ = ["SessionLocal"]
