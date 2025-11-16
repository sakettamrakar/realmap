"""CLI tool to geocode projects missing coordinates."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from cg_rera_extractor.config.loader import load_config
from cg_rera_extractor.config.models import AppConfig, DatabaseConfig
from cg_rera_extractor.db import get_engine, get_session_local
from cg_rera_extractor.geo import NoopGeocoder, geocode_missing_projects


def load_db_config(config_path: str | None) -> DatabaseConfig:
    """Load database configuration from YAML or environment."""

    if config_path:
        resolved_path = Path(config_path).expanduser().resolve()
        app_config: AppConfig = load_config(str(resolved_path))
        return app_config.db

    env_url = os.getenv("DATABASE_URL")
    if not env_url:
        raise ValueError("DATABASE_URL must be set when no config file is provided.")
    return DatabaseConfig(url=env_url)


def main() -> int:
    parser = argparse.ArgumentParser(description="Geocode projects missing coordinates")
    parser.add_argument(
        "--config",
        help="Path to YAML config containing db.url (falls back to DATABASE_URL if omitted)",
    )
    parser.add_argument("--limit", type=int, default=100, help="Maximum projects to geocode")
    parser.add_argument(
        "--mode",
        choices=["noop"],
        default="noop",
        help="Geocoder mode to use (noop only for now)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    db_config = load_db_config(args.config)
    engine = get_engine(db_config)
    SessionLocal = get_session_local(engine)

    geocoder = NoopGeocoder()

    with SessionLocal() as session:
        counts = geocode_missing_projects(session, geocoder, limit=args.limit)
        logging.info("Geocoding run complete: %s", counts)

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
