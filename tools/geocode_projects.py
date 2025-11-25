"""CLI tool to geocode projects missing coordinates."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add tools directory to path to import sibling modules
sys.path.append(str(Path(__file__).parent))

from backfill_normalized_addresses import build_address_parts
from sqlalchemy import select

from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
from cg_rera_extractor.config.loader import load_config
from cg_rera_extractor.config.models import AppConfig, DatabaseConfig, GeocoderConfig, GeocoderProvider
from cg_rera_extractor.db import Project, get_engine, get_session_local
from cg_rera_extractor.geo import GeocodingStatus, build_geocoding_client, generate_geocoding_candidates
from cg_rera_extractor.geo.address_normalizer import AddressParts


def load_configs(config_path: str | None) -> tuple[DatabaseConfig, GeocoderConfig]:
    """Load database and geocoder configs from YAML or environment."""

    if config_path:
        resolved_path = Path(config_path).expanduser().resolve()
        app_config: AppConfig = load_config(str(resolved_path))
        return app_config.db, app_config.geocoder

    env_url = ensure_database_url()
    return DatabaseConfig(url=env_url), GeocoderConfig()


def main() -> int:
    parser = argparse.ArgumentParser(description="Geocode projects missing coordinates")
    parser.add_argument(
        "--config",
        help="Path to YAML config containing db/geocoder settings (falls back to environment if omitted)",
    )
    parser.add_argument("--limit", type=int, default=100, help="Maximum projects to geocode")
    parser.add_argument(
        "--provider",
        choices=[provider.value for provider in GeocoderProvider],
        help="Override configured geocoder provider",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without committing updates to the database",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    db_config, geocoder_config = load_configs(args.config)
    engine = get_engine(db_config)
    SessionLocal = get_session_local(engine)
    logging.info("Connected to %s", describe_database_target(db_config.url))

    geocoding_client = build_geocoding_client(geocoder_config, provider_override=args.provider)

    with SessionLocal() as session:
        stmt = (
            select(Project)
            .where(Project.normalized_address.is_not(None))
            .where(
                (Project.latitude.is_(None))
                | (Project.longitude.is_(None))
                | (Project.geo_source.is_(None))
            )
            .limit(args.limit)
        )
        projects = session.scalars(stmt).all()
        logging.info("Found %s project(s) needing geocoding", len(projects))

        counts = {"processed": 0, "success": 0, "failed": 0}
        for project in projects:
            counts["processed"] += 1
            
            # Generate candidates for fallback
            parts = build_address_parts(project)
            candidates = generate_geocoding_candidates(parts)
            
            result = None
            used_address = None
            
            for candidate in candidates:
                logging.debug("Trying candidate: %s", candidate)
                result = geocoding_client.geocode(candidate)
                if result:
                    used_address = candidate
                    break
            
            if not result:
                logging.warning("Geocoding failed for project %s (tried %d candidates)", project.id, len(candidates))
                project.geocoding_status = GeocodingStatus.FAILED
                counts["failed"] += 1
                continue

            project.latitude = result.lat
            project.longitude = result.lon
            project.formatted_address = result.formatted_address
            project.geo_precision = result.geo_precision
            project.geo_source = result.geo_source
            project.geo_normalized_address = used_address # Store which address actually worked
            project.geocoding_status = GeocodingStatus.SUCCESS
            counts["success"] += 1
            
            logging.info("Geocoded project %s using: '%s'", project.id, used_address)

        if args.dry_run:
            session.rollback()
            logging.info("Dry run enabled; no database updates committed")
        else:
            session.commit()
            logging.info("Committed geocoding updates")

    logging.info("Geocoding run complete: %s", counts)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
