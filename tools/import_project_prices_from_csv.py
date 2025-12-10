"""Import project prices from CSV."""
import argparse
import csv
import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from cg_rera_extractor.config.env import ensure_database_url
from cg_rera_extractor.db import (
    Project,
    ProjectPricingSnapshot,
    ProjectUnitType,
    get_engine,
    get_session_local,
)

logger = logging.getLogger(__name__)

def parse_decimal(value: str | None) -> Decimal | None:
    if not value or value.strip() == "":
        return None
    try:
        return Decimal(value.strip())
    except Exception:
        return None

def import_prices(csv_path: str, snapshot_date: date, source_type: str) -> None:
    ensure_database_url()
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    session = SessionLocal()

    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        logger.info(f"Read {len(rows)} rows from {csv_path}")
        
        projects_cache = {}
        
        for row in rows:
            reg_no = row.get("project_reg_no")
            if not reg_no:
                logger.warning("Skipping row without project_reg_no")
                continue
                
            # Normalize reg no if needed (e.g. strip state code if user provided full)
            # Assuming user provides what's in DB or suffix.
            # Let's try exact match first.
            
            if reg_no not in projects_cache:
                project = session.execute(
                    select(Project).where(Project.rera_registration_number == reg_no)
                ).scalar_one_or_none()
                
                if not project:
                    # Try suffix match if it contains "-"
                    # e.g. CSV has "PCGRERA..." DB has "CG-PCGRERA..."
                    # or CSV has "CG-PCGRERA..." DB has "PCGRERA..."
                    # Actually DB has "PCGRERA..." usually stored in rera_registration_number?
                    # Let's check DB content. Usually it's the number.
                    # Let's try strict match first.
                    logger.warning(f"Project not found for reg_no: {reg_no}")
                    continue
                projects_cache[reg_no] = project
            
            project = projects_cache[reg_no]
            
            unit_label = row.get("unit_label")
            min_price = parse_decimal(row.get("min_price_total"))
            max_price = parse_decimal(row.get("max_price_total"))
            min_sqft = parse_decimal(row.get("min_price_per_sqft"))
            max_sqft = parse_decimal(row.get("max_price_per_sqft"))
            source_ref = row.get("source_reference") or csv_path
            
            # 1. Upsert Unit Type if label provided
            if unit_label:
                unit_type = session.execute(
                    select(ProjectUnitType).where(
                        ProjectUnitType.project_id == project.id,
                        ProjectUnitType.unit_label == unit_label
                    )
                ).scalar_one_or_none()
                
                if not unit_type:
                    unit_type = ProjectUnitType(
                        project_id=project.id,
                        unit_label=unit_label,
                        is_active=True
                    )
                    session.add(unit_type)
                    session.flush() # Get ID
            
            # 2. Upsert Pricing Snapshot
            # Check if snapshot exists for this date and unit label (or None)
            stmt = select(ProjectPricingSnapshot).where(
                ProjectPricingSnapshot.project_id == project.id,
                ProjectPricingSnapshot.snapshot_date == snapshot_date,
                ProjectPricingSnapshot.source_type == source_type
            )
            
            if unit_label:
                stmt = stmt.where(ProjectPricingSnapshot.unit_type_label == unit_label)
            else:
                stmt = stmt.where(ProjectPricingSnapshot.unit_type_label.is_(None))
                
            snapshot = session.execute(stmt).scalar_one_or_none()
            
            if snapshot:
                snapshot.min_price_total = min_price
                snapshot.max_price_total = max_price
                snapshot.min_price_per_sqft = min_sqft
                snapshot.max_price_per_sqft = max_sqft
                snapshot.source_reference = source_ref
                snapshot.is_active = True
            else:
                snapshot = ProjectPricingSnapshot(
                    project_id=project.id,
                    snapshot_date=snapshot_date,
                    unit_type_label=unit_label,
                    min_price_total=min_price,
                    max_price_total=max_price,
                    min_price_per_sqft=min_sqft,
                    max_price_per_sqft=max_sqft,
                    source_type=source_type,
                    source_reference=source_ref,
                    is_active=True
                )
                session.add(snapshot)
        
        session.commit()
        logger.info("Import completed successfully.")

    except Exception as e:
        session.rollback()
        logger.error(f"Import failed: {e}")
        raise
    finally:
        session.close()

def main():
    parser = argparse.ArgumentParser(description="Import project prices from CSV")
    parser.add_argument("csv_path", help="Path to CSV file")
    parser.add_argument("--date", help="Snapshot date (YYYY-MM-DD)", default=date.today().isoformat())
    parser.add_argument("--source", help="Source type", default="manual")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    snapshot_date = date.fromisoformat(args.date)
    import_prices(args.csv_path, snapshot_date, args.source)

if __name__ == "__main__":
    main()
