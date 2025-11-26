"""QA script to check scoring coverage and status distribution."""
import sys
import os
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from collections import Counter

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cg_rera_extractor.db import ProjectScores, Project
from cg_rera_extractor.config.env import ensure_database_url

def check_scoring_coverage():
    db_url = ensure_database_url()
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Total projects
        total_projects = session.scalar(select(func.count(Project.id)))
        
        # Total scores
        total_scores = session.scalar(select(func.count(ProjectScores.id)))
        
        print(f"Total Projects: {total_projects}")
        print(f"Projects with Scores: {total_scores}")
        print("-" * 40)

        # Status distribution
        status_counts = session.execute(
            select(ProjectScores.score_status, func.count(ProjectScores.id))
            .group_by(ProjectScores.score_status)
        ).all()

        print("Score Status Distribution:")
        for status, count in status_counts:
            print(f"  {status or 'NULL'}: {count}")
        print("-" * 40)

        # Reasons breakdown
        # score_status_reason is JSONB, but might be stored as list or dict.
        # We'll fetch all and aggregate in python for simplicity.
        reasons = session.execute(select(ProjectScores.score_status_reason)).scalars().all()
        
        reason_counter = Counter()
        for r in reasons:
            if not r:
                continue
            if isinstance(r, list):
                for item in r:
                    reason_counter[item] += 1
            elif isinstance(r, dict):
                # Handle if it's a dict (though logic seems to produce list)
                for k in r.keys():
                    reason_counter[k] += 1
            else:
                reason_counter[str(r)] += 1

        print("Top Missing Data Reasons:")
        for reason, count in reason_counter.most_common(10):
            print(f"  {reason}: {count}")
        print("-" * 40)

        # Sample projects per status
        print("Sample Projects per Status:")
        for status, _ in status_counts:
            status_val = status
            stmt = (
                select(Project.id, Project.project_name, Project.district, ProjectScores.overall_score)
                .join(ProjectScores)
                .where(ProjectScores.score_status == status_val)
                .limit(3)
            )
            samples = session.execute(stmt).all()
            print(f"  Status '{status_val}':")
            for pid, name, dist, score in samples:
                print(f"    - [{pid}] {name} ({dist}): Overall={score}")
            print()

    finally:
        session.close()

if __name__ == "__main__":
    check_scoring_coverage()
