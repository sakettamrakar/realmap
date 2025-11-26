"""Check scoring coverage and status distribution."""
from __future__ import annotations

import logging
from collections import Counter

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from cg_rera_extractor.config.env import ensure_database_url
from cg_rera_extractor.db import ProjectScores, get_engine, get_session_local

def main() -> None:
    ensure_database_url()
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    session = SessionLocal()

    try:
        # Total projects with scores
        total_scores = session.scalar(select(func.count(ProjectScores.id)))
        print(f"Total projects with score records: {total_scores}")

        # Status distribution
        status_counts = session.execute(
            select(ProjectScores.score_status, func.count(ProjectScores.id))
            .group_by(ProjectScores.score_status)
        ).all()

        print("\nScore Status Distribution:")
        for status, count in status_counts:
            print(f"  {status}: {count}")

        # Reasons
        print("\nTop 5 Reasons for Insufficient/Partial Data:")
        reasons = session.scalars(
            select(ProjectScores.score_status_reason)
            .where(ProjectScores.score_status != 'ok')
        ).all()
        
        flat_reasons = []
        for r in reasons:
            if isinstance(r, list):
                flat_reasons.extend(r)
            elif isinstance(r, str):
                flat_reasons.append(r)
        
        for reason, count in Counter(flat_reasons).most_common(5):
            print(f"  {reason}: {count}")

    finally:
        session.close()

if __name__ == "__main__":
    main()
