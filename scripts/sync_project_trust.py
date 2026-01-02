"""
Script to aggregate trust markers from RERA filings and update Project trust fields.
"""
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from cg_rera_extractor.db import get_engine, get_session_local, Project, ReraFiling

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_trust_markers(sample_mode: bool = False, session: Session = None):
    if session is None:
        engine = get_engine()
        SessionLocal = get_session_local(engine)
        session = SessionLocal()
        own_session = True
    else:
        own_session = False

    try:
        # Fetch all projects
        stmt = select(Project)
        projects = session.execute(stmt).scalars().all()

        for project in projects:
            logger.info(f"Processing trust markers for project: {project.project_name} ({project.rera_registration_number})")
            
            # Fetch filings for this project
            filing_stmt = select(ReraFiling).where(ReraFiling.project_id == project.id)
            filings = session.execute(filing_stmt).scalars().all()

            if not filings:
                logger.debug(f"No filings found for project {project.id}")
                continue

            # Aggregate logic
            latest_audit_date = None
            max_completion = 0.0
            current_status = "ACTIVE"

            for filing in filings:
                # Update status if revoked in any filing
                if filing.extracted_data and filing.extracted_data.get("status") == "REVOKED":
                    current_status = "REVOKED"
                
                # Track latest audit date
                if filing.processed_at:
                    if not latest_audit_date or filing.processed_at > latest_audit_date:
                        latest_audit_date = filing.processed_at

                # Track max completion percentage
                if filing.extracted_data:
                    comp = filing.extracted_data.get("completion_percent", 0)
                    try:
                        comp_val = float(comp)
                        if comp_val > max_completion:
                            max_completion = comp_val
                    except (ValueError, TypeError):
                        pass

            # Update project fields
            project.rera_status = current_status
            project.construction_completion_percent = max_completion
            if latest_audit_date:
                project.last_financial_audit_date = latest_audit_date.date()
            
            logger.info(f"Updated {project.project_name}: Status={current_status}, Completion={max_completion}%")

        if not sample_mode:
            session.commit()
            logger.info("Trust markers synced successfully.")
        else:
            logger.info("Sample mode: Changes not committed.")

    except Exception as e:
        if own_session:
            session.rollback()
        logger.error(f"Error syncing trust markers: {e}")
        raise e
    finally:
        if own_session:
            session.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true", help="Run in sample mode without committing")
    args = parser.parse_args()
    
    sync_trust_markers(sample_mode=args.sample)
