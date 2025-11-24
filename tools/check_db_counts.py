


"""Quick database verification helper to check row counts in key tables."""
from __future__ import annotations

import argparse
from typing import Optional

from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
from cg_rera_extractor.db import (
    Building,
    Project,
    ProjectDocument,
    Promoter,
    QuarterlyUpdate,
    UnitType,
    get_engine,
    get_session_local,
)


def get_total_counts(session: Session) -> dict[str, int]:
    """Fetch total row counts from all main tables."""
    counts = {}
    
    counts["projects"] = session.execute(select(func.count(Project.id))).scalar() or 0
    counts["promoters"] = session.execute(select(func.count(Promoter.id))).scalar() or 0
    counts["buildings"] = session.execute(select(func.count(Building.id))).scalar() or 0
    counts["unit_types"] = session.execute(select(func.count(UnitType.id))).scalar() or 0
    counts["documents"] = session.execute(select(func.count(ProjectDocument.id))).scalar() or 0
    counts["quarterly_updates"] = session.execute(select(func.count(QuarterlyUpdate.id))).scalar() or 0
    
    return counts


def report_geo_columns(engine) -> tuple[list[str], list[str]]:
    """Report presence of expected GEO columns on the projects table."""

    expected_geo_columns = {
        "latitude",
        "longitude",
        "geocoding_status",
        "geocoding_source",
        "geo_source",
        "geo_precision",
        "geo_confidence",
        "geo_normalized_address",
        "geo_formatted_address",
    }

    inspector = inspect(engine)
    existing = {col["name"] for col in inspector.get_columns("projects")}

    present = sorted(expected_geo_columns & existing)
    missing = sorted(expected_geo_columns - existing)
    return present, missing


def get_project_by_reg(session: Session, state_code: str, reg_number: str) -> Optional[Project]:
    """Fetch a project by state code and registration number."""
    stmt = select(Project).where(
        Project.state_code == state_code,
        Project.rera_registration_number == reg_number,
    )
    return session.execute(stmt).scalar_one_or_none()


def get_project_children_counts(session: Session, project_id: int) -> dict[str, int]:
    """Get counts of child records for a specific project."""
    counts = {}
    
    counts["promoters"] = session.execute(
        select(func.count(Promoter.id)).where(Promoter.project_id == project_id)
    ).scalar() or 0
    
    counts["buildings"] = session.execute(
        select(func.count(Building.id)).where(Building.project_id == project_id)
    ).scalar() or 0
    
    counts["unit_types"] = session.execute(
        select(func.count(UnitType.id)).where(UnitType.project_id == project_id)
    ).scalar() or 0
    
    counts["documents"] = session.execute(
        select(func.count(ProjectDocument.id)).where(ProjectDocument.project_id == project_id)
    ).scalar() or 0
    
    counts["quarterly_updates"] = session.execute(
        select(func.count(QuarterlyUpdate.id)).where(QuarterlyUpdate.project_id == project_id)
    ).scalar() or 0
    
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check row counts in the CG RERA database"
    )
    parser.add_argument(
        "--project-reg",
        help="Project registration number (e.g., CG-2024-00123) to get details for",
    )
    parser.add_argument(
        "--state-code",
        default="CG",
        help="State code for project lookup (default: CG)",
    )
    parser.add_argument(
        "--district",
        help="Filter by district (planned for future)",
    )
    
    args = parser.parse_args()
    
    # Connect to database
    db_url = ensure_database_url()
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    session = SessionLocal()
    
    try:
        print(f"\n{'='*70}")
        print(f"Database Row Counts")
        print(f"{'='*70}")
        print(f"Database: {describe_database_target(db_url)}")
        print()
        
        # Get total counts
        totals = get_total_counts(session)
        
        print("Total Rows:")
        print(f"  Projects:          {totals['projects']:>10,}")
        print(f"  Promoters:         {totals['promoters']:>10,}")
        print(f"  Buildings:         {totals['buildings']:>10,}")
        print(f"  Unit Types:        {totals['unit_types']:>10,}")
        print(f"  Documents:         {totals['documents']:>10,}")
        print(f"  Quarterly Updates: {totals['quarterly_updates']:>10,}")

        print(f"\n  TOTAL RECORDS:     {sum(totals.values()):>10,}")

        present_geo, missing_geo = report_geo_columns(engine)
        print("\nGEO Columns (projects table):")
        print(f"  Present: {', '.join(present_geo) if present_geo else 'none'}")
        print(
            f"  Missing: {', '.join(missing_geo) if missing_geo else 'none'}"
        )
        
        # If project filter requested, show details
        if args.project_reg:
            print(f"\n{'-'*70}")
            print(f"Project Details: {args.state_code}-{args.project_reg}")
            print(f"{'-'*70}")
            
            # Parse project reg - if it already includes state, extract just the number
            reg_number = args.project_reg
            if "-" in args.project_reg:
                parts = args.project_reg.split("-")
                if len(parts) >= 2:
                    reg_number = "-".join(parts[1:])  # Handle CG-2024-00123 format
            
            project = get_project_by_reg(session, args.state_code, reg_number)
            
            if not project:
                print(f"✗ Project not found: {args.state_code}-{reg_number}")
                return 1
            
            print(f"Project ID:        {project.id}")
            print(f"Project Name:      {project.project_name}")
            print(f"Status:            {project.status}")
            print(f"District:          {project.district}")
            print(f"Tehsil:            {project.tehsil}")
            print(f"Address:           {project.full_address}")
            
            child_counts = get_project_children_counts(session, project.id)
            print(f"\nChild Records:")
            print(f"  Promoters:         {child_counts['promoters']:>10,}")
            print(f"  Buildings:         {child_counts['buildings']:>10,}")
            print(f"  Unit Types:        {child_counts['unit_types']:>10,}")
            print(f"  Documents:         {child_counts['documents']:>10,}")
            print(f"  Quarterly Updates: {child_counts['quarterly_updates']:>10,}")
            print(f"  TOTAL CHILDREN:    {sum(child_counts.values()):>10,}")
        
        print(f"\n{'='*70}\n")
        return 0
        
    except Exception as exc:
        print(f"\n✗ Error: {exc}\n")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
