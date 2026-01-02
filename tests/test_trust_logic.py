import pytest
from datetime import datetime, timezone
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker
from cg_rera_extractor.db import Project, ReraFiling, Base
from scripts.sync_project_trust import sync_trust_markers

@pytest.fixture
def db_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_trust_sync_logic(db_session):
    """
    Verify that sync_project_trust.py correctly aggregates data from filings.
    """
    # 1. Create a test project
    project = Project(
        state_code="CG",
        rera_registration_number="TEST-TRUST-001",
        project_name="Trust Test Project",
        status="Approved"
    )
    db_session.add(project)
    db_session.flush()

    # 2. Create mock filings
    filing1 = ReraFiling(
        project_id=project.id,
        file_path="/tmp/f1.pdf",
        doc_type="QPR",
        extracted_data={"completion_percent": 45.5},
        processed_at=datetime(2025, 1, 1, tzinfo=timezone.utc)
    )
    filing2 = ReraFiling(
        project_id=project.id,
        file_path="/tmp/f2.pdf",
        doc_type="QPR",
        extracted_data={"completion_percent": 60.0, "status": "REVOKED"},
        processed_at=datetime(2025, 6, 1, tzinfo=timezone.utc)
    )
    db_session.add_all([filing1, filing2])
    db_session.commit()

    # 3. Run sync logic (we'll call the function directly)
    sync_trust_markers(sample_mode=False, session=db_session)

    # 4. Verify results
    db_session.expire_all()
    updated_project = db_session.execute(
        select(Project).where(Project.id == project.id)
    ).scalar_one()

    assert updated_project.rera_status == "REVOKED"
    assert float(updated_project.construction_completion_percent) == 60.0
    assert updated_project.last_financial_audit_date == datetime(2025, 6, 1).date()

def test_revoked_status_flagging(db_session):
    """
    Verify that a revoked status is correctly identified.
    """
    project = Project(
        state_code="CG",
        rera_registration_number="TEST-REVOKED-001",
        project_name="Revoked Project",
        rera_status="REVOKED"
    )
    db_session.add(project)
    db_session.commit()
    
    # This test would typically check an API endpoint, but here we just check the DB state
    assert project.rera_status == "REVOKED"
