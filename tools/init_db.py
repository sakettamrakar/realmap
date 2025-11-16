"""Initialize the CG RERA database schema."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from cg_rera_extractor.config.loader import load_config
from cg_rera_extractor.config.models import AppConfig, DatabaseConfig
from cg_rera_extractor.db.base import get_engine
from cg_rera_extractor.db.init_db import init_db


def load_db_config(config_path: str | None) -> DatabaseConfig:
    """Load :class:`DatabaseConfig` from a YAML file or the environment."""

    if config_path:
        resolved_path = Path(config_path).expanduser().resolve()
        app_config: AppConfig = load_config(str(resolved_path))
        return app_config.db

    env_url = os.getenv("DATABASE_URL")
    if not env_url:
        raise ValueError("DATABASE_URL must be set when no config file is provided.")
    return DatabaseConfig(url=env_url)


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize the Postgres schema for CG RERA projects.")
    parser.add_argument(
        "--config",
        help="Path to YAML config containing db.url (falls back to DATABASE_URL if omitted)",
    )
    args = parser.parse_args()

    db_config = load_db_config(args.config)
    engine = get_engine(db_config)
    init_db(engine)
    print(f"Initialized database schema using {db_config.url}")


if __name__ == "__main__":
    main()
