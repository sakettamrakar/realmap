"""Apply idempotent database migrations for the CG RERA schema."""
from __future__ import annotations

from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
from cg_rera_extractor.db import apply_migrations, get_engine


def main() -> int:
    db_url = ensure_database_url()
    engine = get_engine()

    print("Applying migrations")
    print(f"Database: {describe_database_target(db_url)}")

    applied = apply_migrations(engine)
    print(f"Migrations invoked: {', '.join(applied) if applied else 'none'}")

    if applied:
        print("\nMigrations complete.")
    else:
        print("\nNo migrations found.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
