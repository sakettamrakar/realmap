"""Populate ``normalized_address`` for existing project rows."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
from cg_rera_extractor.config.loader import load_config
from cg_rera_extractor.config.models import AppConfig, DatabaseConfig
from cg_rera_extractor.db import Project, get_engine, get_session_local
from cg_rera_extractor.geo import AddressParts, normalize_address

logger = logging.getLogger(__name__)


def load_db_config(config_path: str | None) -> DatabaseConfig:
    """Load database configuration from YAML or environment."""

    if config_path:
        resolved_path = Path(config_path).expanduser().resolve()
        app_config: AppConfig = load_config(str(resolved_path))
        return app_config.db

    env_url = ensure_database_url()
    return DatabaseConfig(url=env_url)


def _first_non_empty(values: list[str | None]) -> str | None:
    for value in values:
        if value and str(value).strip():
            return str(value)
    return None


def build_address_parts(project: Project) -> AddressParts:
    raw_data: dict[str, Any] = project.raw_data_json or {}
    raw_details: dict[str, Any] = raw_data.get("project_details", {}) if isinstance(raw_data, dict) else {}
    metadata: dict[str, Any] = raw_data.get("metadata", {}) if isinstance(raw_data, dict) else {}

    return AddressParts(
        address_line=_first_non_empty([project.full_address, raw_details.get("project_address")]),
        village_or_locality=_first_non_empty(
            [project.village_or_locality, raw_details.get("village_or_locality")]
        ),
        tehsil=_first_non_empty([project.tehsil, raw_details.get("tehsil")]),
        district=_first_non_empty([project.district, raw_details.get("district")]),
        state=_first_non_empty([raw_details.get("state")]),
        state_code=_first_non_empty([project.state_code, metadata.get("state_code")]),
        pincode=_first_non_empty([project.pincode, raw_details.get("pincode")]),
        country="India",
    )


class BackfillStats(dict):
    """Simple dict-backed accumulator for script stats."""

    def __init__(self) -> None:  # pragma: no cover - trivial wrapper
        super().__init__(processed=0, updated=0, weak=0, skipped_empty=0)


def backfill_normalized_addresses(session: Session, limit: int | None = None, dry_run: bool = False) -> BackfillStats:
    """Populate ``normalized_address`` for projects missing a value."""

    stats = BackfillStats()
    stmt = select(Project).where(
        (Project.normalized_address.is_(None)) | (Project.normalized_address == "")
    )
    if limit:
        stmt = stmt.limit(limit)

    projects = session.scalars(stmt).all()
    for project in projects:
        stats["processed"] += 1
        parts = build_address_parts(project)
        normalized = normalize_address(parts)

        if not normalized.normalized_address:
            stats["skipped_empty"] += 1
            logger.info(
                "Skipping project %s: insufficient address parts", project.rera_registration_number
            )
            continue

        if normalized.is_low_confidence:
            stats["weak"] += 1

        if dry_run:
            logger.info(
                "Would update %s -> %s",
                project.rera_registration_number,
                normalized.normalized_address,
            )
            continue

        project.normalized_address = normalized.normalized_address
        stats["updated"] += 1

    if not dry_run:
        session.commit()
    else:  # pragma: no cover - CLI side effect
        session.rollback()

    return stats


def main() -> int:  # pragma: no cover - CLI entry point
    parser = argparse.ArgumentParser(description="Backfill normalized addresses for projects")
    parser.add_argument(
        "--config",
        help="Path to YAML config containing db.url (falls back to DATABASE_URL if omitted)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit number of projects processed")
    parser.add_argument(
        "--dry-run", action="store_true", help="Log updates without writing to the database"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    db_config = load_db_config(args.config)
    engine = get_engine(db_config)
    SessionLocal = get_session_local(engine)
    logger.info("Connected to %s", describe_database_target(db_config.url))

    with SessionLocal() as session:
        stats = backfill_normalized_addresses(session, limit=args.limit, dry_run=args.dry_run)
        logger.info("Backfill completed: %s", dict(stats))

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
