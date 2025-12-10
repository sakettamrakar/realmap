"""Initialize the CG RERA database schema."""
from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import inspect

from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
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

    env_url = ensure_database_url()
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
    
    print("Initializing database schema...")
    print(f"Database target: {describe_database_target(db_config.url)}")
    
    init_db(engine)
    
    # Verify tables were created
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("\n✓ Schema initialized successfully!")
    print(f"\nTables created ({len(tables)} total):")
    for table_name in sorted(tables):
        print(f"  • {table_name}")
    
    if not tables:
        print("  ⚠ WARNING: No tables found! Check database connectivity.")


if __name__ == "__main__":
    main()
