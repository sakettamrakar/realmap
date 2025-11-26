"""Batch job to compute amenity-based project scores."""
from __future__ import annotations

import argparse
import logging
from collections import defaultdict
from datetime import datetime, timezone
from statistics import mean
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from cg_rera_extractor.amenities import compute_amenity_scores
from cg_rera_extractor.config.env import describe_database_target, ensure_database_url
from cg_rera_extractor.db import (
    Project,
    ProjectAmenityStats,
    ProjectScores,
    get_engine,
    get_session_local,
)

logger = logging.getLogger(__name__)


# ---- DB helpers ----------------------------------------------------------

def _project_ids_with_stats(
    session: Session,
    *,
    project_id: int | None,
    project_reg: str | None,
    limit: int | None,
) -> list[tuple[int, str | None, str | None]]:
    stmt = (
        select(Project.id, Project.state_code, Project.rera_registration_number)
        .join(ProjectAmenityStats)
        .group_by(Project.id)
        .order_by(Project.id)
    )

    if project_id:
        stmt = stmt.where(Project.id == project_id)
    if project_reg:
        stmt = stmt.where(Project.rera_registration_number == project_reg)
    if limit:
        stmt = stmt.limit(limit)

    return session.execute(stmt).all()


# ---- Scoring -------------------------------------------------------------

def _fetch_stats_for_project(session: Session, project_id: int) -> Iterable[ProjectAmenityStats]:
    stmt = select(ProjectAmenityStats).where(ProjectAmenityStats.project_id == project_id)
    return session.scalars(stmt).all()


def _upsert_score(session: Session, project_id: int, scores: ProjectScores) -> ProjectScores:
    existing = session.execute(
        select(ProjectScores).where(ProjectScores.project_id == project_id)
    ).scalar_one_or_none()
    if existing:
        existing.amenity_score = scores.amenity_score
        existing.location_score = scores.location_score
        existing.connectivity_score = scores.connectivity_score
        existing.daily_needs_score = scores.daily_needs_score
        existing.social_infra_score = scores.social_infra_score
        existing.overall_score = scores.overall_score
        existing.score_status = scores.score_status
        existing.score_status_reason = scores.score_status_reason
        existing.score_version = scores.score_version
        existing.last_computed_at = datetime.now(timezone.utc)
        return existing

    session.add(scores)
    return scores


# ---- CLI -----------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Compute amenity scores for projects")
    parser.add_argument("--limit", type=int, help="Limit number of projects to score")
    parser.add_argument("--project-id", type=int, help="Score a single project by ID")
    parser.add_argument(
        "--project-reg",
        help="Score a single project by registration number (without state prefix)",
    )
    parser.add_argument(
        "--recompute", action="store_true", help="Overwrite existing scores"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )

    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level))

    db_url = ensure_database_url()
    engine = get_engine()
    SessionLocal = get_session_local(engine)

    session = SessionLocal()
    scored_overall: list[float] = []
    missing_summary: defaultdict[str, int] = defaultdict(int)
    sample_logs: list[str] = []

    try:
        project_reg = args.project_reg
        if project_reg and "-" in project_reg:
            project_reg = project_reg.split("-", 1)[1]

        project_rows = _project_ids_with_stats(
            session,
            project_id=args.project_id,
            project_reg=project_reg,
            limit=args.limit,
        )
        logger.info(
            "Preparing to score %s projects (database: %s)",
            len(project_rows),
            describe_database_target(db_url),
        )

        for project_id, state_code, reg in project_rows:
            # Skip already-scored projects unless recompute is requested.
            if not args.recompute:
                existing = session.execute(
                    select(ProjectScores.overall_score).where(
                        ProjectScores.project_id == project_id
                    )
                ).scalar_one_or_none()
                if existing is not None:
                    logger.debug("Skipping project %s (score exists)", project_id)
                    continue

            stats = _fetch_stats_for_project(session, project_id)
            if not stats:
                logger.warning(
                    "Project %s has no amenity stats; cannot compute scores", project_id
                )
                continue

            computation = compute_amenity_scores(stats)
            scores = ProjectScores(
                project_id=project_id,
                amenity_score=computation.scores.amenity_score,
                location_score=computation.scores.location_score,
                connectivity_score=computation.scores.connectivity_score,
                daily_needs_score=computation.scores.daily_needs_score,
                social_infra_score=computation.scores.social_infra_score,
                overall_score=computation.scores.overall_score,
                score_status=computation.scores.score_status,
                score_status_reason=computation.scores.score_status_reason,
                score_version=computation.scores.score_version,
                last_computed_at=datetime.now(timezone.utc),
            )

            # Scores are already clamped to [0, 100] by compute_amenity_scores.
            _upsert_score(session, project_id, scores)
            session.commit()

            if scores.overall_score is not None:
                scored_overall.append(float(scores.overall_score))
            
            for missing_key in computation.missing_inputs:
                missing_summary[missing_key] += 1

            if len(sample_logs) < 5:
                sample_logs.append(
                    (
                        f"Project {project_id} ({state_code}-{reg}): "
                        f"status={scores.score_status}, overall={scores.overall_score}, loc={scores.location_score}, amenity={scores.amenity_score}; "
                        f"daily={scores.daily_needs_score}, social={scores.social_infra_score}, conn={scores.connectivity_score}; "
                        f"inputs={computation.inputs_used}"
                    )
                )

        if scored_overall:
            logger.info(
                "Scored %s projects | overall min=%.1f mean=%.1f max=%.1f",
                len(scored_overall),
                min(scored_overall),
                mean(scored_overall),
                max(scored_overall),
            )
        else:
            logger.info("No projects were scored (did scores already exist?)")

        if missing_summary:
            logger.info("Missing input counts (amenity slices absent in stats):")
            for key, count in sorted(missing_summary.items(), key=lambda kv: kv[1], reverse=True):
                logger.info("  %s: %s projects", key, count)

        if sample_logs:
            logger.info("Sample computations:")
            for line in sample_logs:
                logger.info("  %s", line)

    finally:
        session.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
