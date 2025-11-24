from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path
from typing import Iterable

from sqlalchemy import delete, select

from cg_rera_extractor.amenities import (
    AmenityCache,
    compute_project_amenity_stats,
    get_provider_from_config,
    to_orm_rows,
)
from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
from cg_rera_extractor.config.loader import load_config
from cg_rera_extractor.config.models import AppConfig, AmenitiesConfig, AmenityProvider, DatabaseConfig
from cg_rera_extractor.db import Project, ProjectAmenityStats, get_engine, get_session_local

logger = logging.getLogger(__name__)


def load_configs(config_path: str | None) -> tuple[DatabaseConfig, AmenitiesConfig]:
    """Load database and amenity configs from YAML or environment."""

    if config_path:
        resolved_path = Path(config_path).expanduser().resolve()
        app_config: AppConfig = load_config(str(resolved_path))
        return app_config.db, app_config.amenities

    env_url = ensure_database_url()
    return DatabaseConfig(url=env_url), AmenitiesConfig()


def _resolve_project_ids(
    session_local, project_ids: Iterable[int] | None, project_regs: Iterable[str] | None, limit: int | None
) -> list[Project]:
    with session_local() as session:
        stmt = (
            select(Project)
            .where(Project.latitude.is_not(None))
            .where(Project.longitude.is_not(None))
        )
        if project_ids:
            stmt = stmt.where(Project.id.in_(list(project_ids)))
        if project_regs:
            stmt = stmt.where(Project.rera_registration_number.in_(list(project_regs)))
        if limit:
            stmt = stmt.limit(limit)
        return session.scalars(stmt).all()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute per-project amenity statistics")
    parser.add_argument("--config", help="Path to YAML config containing db/amenity settings (defaults to env vars)")
    parser.add_argument("--limit", type=int, help="Process only the first N matching projects")
    parser.add_argument("--project-id", action="append", type=int, help="Specific project ID(s) to process")
    parser.add_argument(
        "--project-reg",
        action="append",
        help="Specific registration number(s) to process (state prefix optional)",
    )
    parser.add_argument(
        "--recompute",
        action="store_true",
        help="Recompute stats even if rows already exist (deletes existing slices first)",
    )
    parser.add_argument(
        "--provider",
        choices=[provider.value for provider in AmenityProvider],
        help="Override configured amenity provider",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    db_config, amenity_config = load_configs(args.config)
    if args.provider:
        amenity_config.provider = AmenityProvider(args.provider)

    engine = get_engine(db_config)
    SessionLocal = get_session_local(engine)
    logger.info("Connected to %s", describe_database_target(db_config.url))

    provider = get_provider_from_config(amenity_config)
    amenity_cache = AmenityCache(provider=provider, session_factory=SessionLocal)

    projects = _resolve_project_ids(SessionLocal, args.project_id, args.project_reg, args.limit)
    if not projects:
        logger.info("No projects matched the filters; exiting")
        return 0

    project_ids = [project.id for project in projects]
    provider_snapshot = provider.name

    existing_ids: set[int] = set()
    with SessionLocal() as session:
        if args.recompute:
            session.execute(
                delete(ProjectAmenityStats).where(ProjectAmenityStats.project_id.in_(project_ids))
            )
            session.commit()
            logger.info("Deleted existing amenity stats for %s project(s)", len(project_ids))
        else:
            existing_ids = set(
                session.scalars(
                    select(ProjectAmenityStats.project_id).where(
                        ProjectAmenityStats.project_id.in_(project_ids)
                    )
                )
            )

    processed = 0
    inserted_rows = 0
    skipped = 0
    started_at = time.time()

    for project in projects:
        if not args.recompute and project.id in existing_ids:
            skipped += 1
            continue

        stats = compute_project_amenity_stats(
            lat=float(project.latitude),
            lon=float(project.longitude),
            amenity_cache=amenity_cache,
            search_radii_km=amenity_config.search_radii_km,
        )
        rows = to_orm_rows(project.id, stats, provider_snapshot=provider_snapshot)

        with SessionLocal() as session:
            session.add_all(rows)
            session.commit()

        processed += 1
        inserted_rows += len(rows)

        if processed and processed % 25 == 0:
            elapsed = time.time() - started_at
            rate = (elapsed / processed * 100) if processed else 0
            logger.info(
                "Processed %s/%s projects (%.1f s elapsed, %.1f s per 100 projects)",
                processed,
                len(projects),
                elapsed,
                rate,
            )

    elapsed = time.time() - started_at
    logger.info(
        "Amenity stats run complete: processed=%s skipped=%s rows_inserted=%s elapsed=%.1fs",
        processed,
        skipped,
        inserted_rows,
        elapsed,
    )
    logger.info(
        "Provider calls: %s | Cache hits: %s",
        amenity_cache.provider_calls,
        amenity_cache.cache_hits,
    )

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
