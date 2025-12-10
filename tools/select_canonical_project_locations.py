"""CLI tool to select and apply canonical locations for projects."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add tools directory to path to import sibling modules
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
from cg_rera_extractor.config.loader import load_config
from cg_rera_extractor.config.models import AppConfig, DatabaseConfig
from cg_rera_extractor.db import Project, get_engine, get_session_local
from cg_rera_extractor.geo.location_selector import apply_canonical_location, select_canonical_location


def load_db_config(config_path: str | None) -> DatabaseConfig:
    if config_path:
        resolved_path = Path(config_path).expanduser().resolve()
        app_config: AppConfig = load_config(str(resolved_path))
        return app_config.db
    env_url = ensure_database_url()
    return DatabaseConfig(url=env_url)


def main() -> int:
    parser = argparse.ArgumentParser(description="Select canonical locations for projects")
    parser.add_argument(
        "--config",
        help="Path to YAML config containing db settings",
    )
    parser.add_argument("--limit", type=int, default=None, help="Maximum projects to process")
    parser.add_argument("--project-id", type=int, help="Process specific project ID")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without committing updates to the database",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    db_config = load_db_config(args.config)
    engine = get_engine(db_config)
    SessionLocal = get_session_local(engine)
    logging.info("Connected to %s", describe_database_target(db_config.url))

    with SessionLocal() as session:
        stmt = select(Project).options(joinedload(Project.locations))
        
        if args.project_id:
            stmt = stmt.where(Project.id == args.project_id)
        
        if args.limit:
            stmt = stmt.limit(args.limit)

        projects = session.scalars(stmt).unique().all()
        logging.info("Found %s project(s) to process", len(projects))

        counts = {"updated": 0, "no_location": 0, "unchanged": 0}
        
        for project in projects:
            best_loc = select_canonical_location(project)
            
            if apply_canonical_location(project, best_loc):
                counts["updated"] += 1
                logging.debug("Updated project %s to %s (%s)", project.id, best_loc.source_type, best_loc.precision_level)
            else:
                if not best_loc:
                    counts["no_location"] += 1
                else:
                    counts["unchanged"] += 1

        if args.dry_run:
            session.rollback()
            logging.info("Dry run enabled; no database updates committed")
        else:
            session.commit()
            logging.info("Committed updates")

    logging.info("Selection run complete: %s", counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
