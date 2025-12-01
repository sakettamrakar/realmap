"""
Utilities for loading V1 scraper outputs into the database.

Point 27 & 29 Integration:
- QA validation gates during ingestion
- DataProvenance records for audit trail
- IngestionAudit tracking for run-level metrics
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from cg_rera_extractor.db import (
    Building,
    Project,
    ProjectDocument,
    ProjectLocation,
    Promoter,
    QuarterlyUpdate,
    UnitType,
    BankAccount,
    LandParcel,
    ProjectArtifact,
    get_engine,
    get_session_local,
)
from cg_rera_extractor.db.models import DataProvenance, IngestionAudit
from cg_rera_extractor.geo import AddressParts, normalize_address
from cg_rera_extractor.parsing.schema import V1Project
from cg_rera_extractor.quality.validation import (
    run_qa_validation,
    QAResult,
    QAStatus,
    PriceSanityConfig,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LoadStats:
    """Aggregated counts produced by the loader."""

    projects_upserted: int = 0
    promoters: int = 0
    buildings: int = 0
    unit_types: int = 0
    documents: int = 0
    quarterly_updates: int = 0
    bank_accounts: int = 0
    land_parcels: int = 0
    artifacts: int = 0
    locations: int = 0
    provenance_records: int = 0  # Point 29: Provenance tracking
    qa_passed: int = 0           # Point 27: QA tracking
    qa_warnings: int = 0
    qa_failed: int = 0
    runs_processed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, int | list[str]]:
        return {
            "projects_upserted": self.projects_upserted,
            "promoters": self.promoters,
            "buildings": self.buildings,
            "unit_types": self.unit_types,
            "documents": self.documents,
            "quarterly_updates": self.quarterly_updates,
            "bank_accounts": self.bank_accounts,
            "land_parcels": self.land_parcels,
            "artifacts": self.artifacts,
            "locations": self.locations,
            "provenance_records": self.provenance_records,
            "qa_passed": self.qa_passed,
            "qa_warnings": self.qa_warnings,
            "qa_failed": self.qa_failed,
            "runs_processed": list(self.runs_processed),
        }


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _to_decimal(value: float | int | str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (ValueError, ArithmeticError):
        return None


def _ensure_session(session: Session | None) -> tuple[Session, Callable[[], None]]:
    if session is not None:
        return session, lambda: None

    engine = get_engine()
    SessionLocal = get_session_local(engine)
    db_session = SessionLocal()
    return db_session, db_session.close


# =============================================================================
# POINT 27: QA Validation Gate
# =============================================================================


def _run_qa_gate(
    v1_project: V1Project,
    config: PriceSanityConfig | None = None,
) -> QAResult:
    """
    Run QA validation on a project before loading.
    
    Point 27: QA gate that validates data quality.
    """
    details = v1_project.project_details
    
    # Build project data dict for validation
    project_data: dict[str, Any] = {
        "rera_registration_number": details.registration_number,
        "project_name": details.project_name,
        "district": details.district,
        "project_status": details.project_status,
        "promoter_name": (
            v1_project.promoter_details[0].name 
            if v1_project.promoter_details else None
        ),
        "approved_date": details.launch_date,
        "proposed_end_date": details.expected_completion_date,
    }
    
    # Extract pricing from unit types if available
    if v1_project.unit_types:
        prices = [ut.price_in_inr for ut in v1_project.unit_types if ut.price_in_inr]
        if prices:
            project_data["min_price_total"] = min(prices)
            project_data["max_price_total"] = max(prices)
    
    return run_qa_validation(project_data, config=config or PriceSanityConfig())


# =============================================================================
# POINT 29: Provenance Record Creation
# =============================================================================


def _create_provenance_record(
    session: Session,
    project_id: int,
    v1_project: V1Project,
    run_id: str | None,
    html_snapshot_path: str | None = None,
    network_log_ref: str | None = None,
) -> DataProvenance:
    """
    Create a DataProvenance record for audit trail.
    
    Point 29: Content Provenance implementation.
    """
    metadata = v1_project.metadata
    
    # Calculate extraction confidence based on field completeness
    total_fields = 10
    filled_fields = sum([
        bool(v1_project.project_details.registration_number),
        bool(v1_project.project_details.project_name),
        bool(v1_project.project_details.district),
        bool(v1_project.project_details.project_status),
        bool(v1_project.promoter_details),
        bool(v1_project.building_details),
        bool(v1_project.unit_types),
        bool(v1_project.documents),
        bool(v1_project.project_details.project_address),
        bool(v1_project.project_details.launch_date),
    ])
    confidence_score = Decimal(str(filled_fields / total_fields))
    
    provenance = DataProvenance(
        project_id=project_id,
        snapshot_url=metadata.source_url,
        source_domain=metadata.source_domain or "rera.cg.gov.in",
        extraction_method=f"v1_json_parser_{metadata.scraper_version or '1.0'}",
        parser_version=metadata.scraper_version,
        confidence_score=confidence_score,
        network_log_ref=network_log_ref,
        html_snapshot_path=html_snapshot_path,
        run_id=run_id,
        scraped_at=datetime.now(timezone.utc),
        fields_extracted=filled_fields,
        fields_expected=total_fields,
    )
    
    session.add(provenance)
    return provenance


def _load_project(
    session: Session,
    v1_project: V1Project,
    run_id: str | None = None,
    html_snapshot_path: str | None = None,
    qa_config: PriceSanityConfig | None = None,
) -> LoadStats:
    stats = LoadStats()
    details = v1_project.project_details

    if not details.registration_number:
        logger.debug(f"Skipping project: empty registration_number (name='{details.project_name}')")
        return stats

    # =========================================================================
    # POINT 27: Run QA Validation Gate
    # =========================================================================
    qa_result = _run_qa_gate(v1_project, config=qa_config)
    
    if qa_result.status == QAStatus.PASSED:
        stats.qa_passed += 1
    elif qa_result.status == QAStatus.WARNING:
        stats.qa_warnings += 1
        logger.warning(
            f"QA warnings for {details.registration_number}: "
            f"{[f.message for f in qa_result.flags]}"
        )
    elif qa_result.status == QAStatus.FAILED:
        stats.qa_failed += 1
        logger.error(
            f"QA failed for {details.registration_number}: "
            f"{[f.message for f in qa_result.flags if f.severity == 'error']}"
        )
        # Continue loading but mark the project

    stmt = select(Project).where(
        Project.state_code == v1_project.metadata.state_code,
        Project.rera_registration_number == details.registration_number,
    )
    project = session.execute(stmt).scalar_one_or_none()

    if project is None:
        project = Project(
            state_code=v1_project.metadata.state_code,
            rera_registration_number=details.registration_number,
            project_name=details.project_name or details.registration_number,
        )
        session.add(project)
    else:
        project.project_name = details.project_name or project.project_name

    project.status = details.project_status
    project.district = details.district
    project.tehsil = details.tehsil
    project.village_or_locality = None
    project.full_address = details.project_address
    project.approved_date = _parse_date(details.launch_date)
    project.proposed_end_date = _parse_date(details.expected_completion_date)
    project.extended_end_date = None
    project.raw_data_json = v1_project.model_dump()

    normalized = normalize_address(
        AddressParts(
            address_line=project.full_address,
            village_or_locality=project.village_or_locality,
            tehsil=project.tehsil,
            district=project.district,
            state_code=project.state_code,
            pincode=project.pincode,
        )
    )
    project.normalized_address = normalized.normalized_address

    # =========================================================================
    # POINT 27: Store QA flags on project
    # =========================================================================
    project.qa_flags = qa_result.to_dict()
    project.qa_status = qa_result.status.value
    project.qa_last_checked_at = qa_result.checked_at

    session.flush()

    # =========================================================================
    # POINT 29: Create DataProvenance record
    # =========================================================================
    _create_provenance_record(
        session=session,
        project_id=project.id,
        v1_project=v1_project,
        run_id=run_id,
        html_snapshot_path=html_snapshot_path,
    )
    stats.provenance_records += 1

    child_tables: list[tuple[type, Iterable]] = [
        (Promoter, v1_project.promoter_details),
        (Building, v1_project.building_details),
        (UnitType, v1_project.unit_types),
        (ProjectDocument, v1_project.documents),
        (QuarterlyUpdate, v1_project.quarterly_updates),
        (BankAccount, v1_project.bank_details),
        (LandParcel, []),  # Land details not directly in V1Project top-level yet
        (ProjectArtifact, []),  # Artifacts handled via previews
        (ProjectLocation, v1_project.rera_locations),  # RERA locations from amenities
    ]
    for model, _ in child_tables:
        session.execute(delete(model).where(model.project_id == project.id))

    # --- Promoters ---
    for promoter in v1_project.promoter_details:
        session.add(
            Promoter(
                project_id=project.id,
                promoter_name=promoter.name or "",
                promoter_type=promoter.organisation_type,
                email=promoter.email,
                phone=promoter.phone,
                address=promoter.address,
                website=None,
            )
        )
        stats.promoters += 1



    # --- Buildings ---
    for building in v1_project.building_details:
        session.add(
            Building(
                project_id=project.id,
                building_name=building.name or "",
                building_type=None,
                number_of_floors=building.number_of_floors,
                total_units=building.number_of_units,
                status=None,
            )
        )
        stats.buildings += 1



    # --- Unit Types ---
    for unit_type in v1_project.unit_types:
        session.add(
            UnitType(
                project_id=project.id,
                type_name=unit_type.name or "",
                carpet_area_sqmt=_to_decimal(unit_type.carpet_area_sq_m),
                saleable_area_sqmt=_to_decimal(unit_type.built_up_area_sq_m),
                total_units=None,
                sale_price=_to_decimal(unit_type.price_in_inr),
            )
        )
        stats.unit_types += 1



    # --- Documents (Legacy) ---
    for doc in v1_project.documents:
        session.add(
            ProjectDocument(
                project_id=project.id,
                doc_type=doc.document_type,
                description=doc.name,
                url=doc.url,
            )
        )
        stats.documents += 1



    # --- Quarterly Updates ---
    for update in v1_project.quarterly_updates:
        quarter_label = " ".join(part for part in [update.quarter, update.year] if part)
        session.add(
            QuarterlyUpdate(
                project_id=project.id,
                quarter=quarter_label or None,
                update_date=None,
                status=update.status,
                summary=update.remarks,
                raw_data_json=update.model_dump(exclude_none=True),
            )
        )
        stats.quarterly_updates += 1

    # --- Bank Accounts ---
    for bank in v1_project.bank_details:
        session.add(
            BankAccount(
                project_id=project.id,
                bank_name=bank.bank_name,
                branch_name=bank.branch_name,
                account_number=bank.account_number,
                ifsc_code=bank.ifsc_code,
                account_holder_name=None,  # Not in V1Project.bank_details
            )
        )
        stats.bank_accounts += 1

    # --- Artifacts (from Previews) ---
    # V1Project doesn't strongly type 'previews' yet, it's in raw_data or a dict
    # We'll try to access it if it exists on the model or raw dict
    previews = getattr(v1_project, "previews", {})
    if not previews and v1_project.raw_data_json:
        previews = v1_project.raw_data_json.get("previews", {})

    if isinstance(previews, dict):
        for field_key, preview_data in previews.items():
            # preview_data might be a dict with 'notes', 'files', etc.
            if isinstance(preview_data, dict):
                notes = preview_data.get("notes")
                # If notes looks like a file path, use it
                file_path = notes if notes and isinstance(notes, str) else None
                
                session.add(
                    ProjectArtifact(
                        project_id=project.id,
                        category="unknown",
                        artifact_type=field_key,
                        file_path=file_path,
                        source_url=None,
                        is_preview=True,
                    )
                )
                stats.artifacts += 1

    # --- RERA Locations (from Amenities) ---
    for rera_loc in v1_project.rera_locations:
        meta_data = {
            "particulars": rera_loc.particulars,
            "image_url": rera_loc.image_url,
            "from_date": rera_loc.from_date,
            "to_date": rera_loc.to_date,
            "progress_percent": rera_loc.progress_percent,
        }
        # Remove None values from metadata
        meta_data = {k: v for k, v in meta_data.items() if v is not None}
        
        session.add(
            ProjectLocation(
                project_id=project.id,
                source_type=rera_loc.source_type,
                lat=_to_decimal(rera_loc.latitude),
                lon=_to_decimal(rera_loc.longitude),
                precision_level="amenity_marker" if rera_loc.source_type == "amenity" else "centroid",
                confidence_score=None,
                is_active=True,
                meta_data=meta_data if meta_data else None,
            )
        )
        stats.locations += 1

    stats.projects_upserted += 1
    return stats


def load_run_into_db(
    run_dir: str,
    session: Session | None = None,
    qa_config: PriceSanityConfig | None = None,
) -> dict:
    """
    Load all V1 JSON files from a single run directory into the DB.
    
    Point 27 & 29 Integration:
    - Creates IngestionAudit record for run tracking
    - Runs QA validation gates on each project
    - Creates DataProvenance records for audit trail
    """

    working_session, cleanup = _ensure_session(session)
    stats = LoadStats()
    run_path = Path(run_dir)
    run_id = run_path.name
    
    # =========================================================================
    # POINT 28: Create IngestionAudit record for this run
    # =========================================================================
    audit = IngestionAudit(
        run_id=run_id,
        run_type="incremental",
        started_at=datetime.now(timezone.utc),
        status="running",
        config_snapshot={"source_dir": str(run_dir)},
    )
    working_session.add(audit)
    working_session.flush()
    
    try:
        json_dir = run_path / "scraped_json"
        v1_files = sorted(json_dir.glob("*.v1.json"))

        logger.info(f"Loading {len(v1_files)} projects from {run_path.name}")
        audit.projects_attempted = len(v1_files)

        for path in v1_files:
            # Determine HTML snapshot path if it exists
            html_path = run_path / "raw_html" / path.name.replace(".v1.json", ".html")
            html_snapshot_path = str(html_path) if html_path.exists() else None
            
            try:
                v1_project = V1Project.model_validate_json(path.read_text())
                project_stats = _load_project(
                    working_session,
                    v1_project,
                    run_id=run_id,
                    html_snapshot_path=html_snapshot_path,
                    qa_config=qa_config,
                )
                stats.projects_upserted += project_stats.projects_upserted
                stats.promoters += project_stats.promoters
                stats.buildings += project_stats.buildings
                stats.unit_types += project_stats.unit_types
                stats.documents += project_stats.documents
                stats.quarterly_updates += project_stats.quarterly_updates
                stats.bank_accounts += project_stats.bank_accounts
                stats.artifacts += project_stats.artifacts
                stats.locations += project_stats.locations
                stats.provenance_records += project_stats.provenance_records
                stats.qa_passed += project_stats.qa_passed
                stats.qa_warnings += project_stats.qa_warnings
                stats.qa_failed += project_stats.qa_failed
            except Exception as exc:
                logger.error(f"Failed to load {path.name}: {exc}")
                raise

        # Update audit record with success metrics
        audit.status = "completed"
        audit.completed_at = datetime.now(timezone.utc)
        audit.projects_succeeded = stats.projects_upserted
        audit.projects_failed = stats.qa_failed
        audit.qa_flags_summary = {
            "qa_passed": stats.qa_passed,
            "qa_warnings": stats.qa_warnings,
            "qa_failed": stats.qa_failed,
        }
        if audit.completed_at and audit.started_at:
            audit.duration_seconds = int(
                (audit.completed_at - audit.started_at).total_seconds()
            )

        working_session.commit()
        logger.info(f"Successfully loaded run {run_path.name}: {stats.to_dict()}")
        return stats.to_dict()
    except Exception as exc:
        logger.error(f"Error loading run {run_dir}: {exc}")
        audit.status = "failed"
        audit.error_log = {"error": str(exc)}
        audit.completed_at = datetime.now(timezone.utc)
        working_session.commit()  # Commit the audit record even on failure
        working_session.rollback()
        raise
    finally:
        cleanup()


def load_all_runs(
    base_runs_dir: str,
    session: Session | None = None,
    qa_config: PriceSanityConfig | None = None,
) -> dict:
    """
    Iterate over all ``run_*`` directories and load them into the DB.
    
    Point 27 & 29 Integration:
    - Aggregates QA statistics across all runs
    - Creates provenance records for all projects
    """

    working_session, cleanup = _ensure_session(session)
    stats = LoadStats()
    try:
        base_path = Path(base_runs_dir)
        run_dirs = sorted(p for p in base_path.glob("run_*") if p.is_dir())
        logger.info(f"Loading {len(run_dirs)} runs from {base_path}")

        for run_path in run_dirs:
            try:
                run_stats = load_run_into_db(
                    str(run_path),
                    session=working_session,
                    qa_config=qa_config,
                )
                stats.projects_upserted += int(run_stats.get("projects_upserted", 0))
                stats.promoters += int(run_stats.get("promoters", 0))
                stats.buildings += int(run_stats.get("buildings", 0))
                stats.unit_types += int(run_stats.get("unit_types", 0))
                stats.documents += int(run_stats.get("documents", 0))
                stats.quarterly_updates += int(run_stats.get("quarterly_updates", 0))
                stats.bank_accounts += int(run_stats.get("bank_accounts", 0))
                stats.artifacts += int(run_stats.get("artifacts", 0))
                stats.locations += int(run_stats.get("locations", 0))
                stats.provenance_records += int(run_stats.get("provenance_records", 0))
                stats.qa_passed += int(run_stats.get("qa_passed", 0))
                stats.qa_warnings += int(run_stats.get("qa_warnings", 0))
                stats.qa_failed += int(run_stats.get("qa_failed", 0))
                stats.runs_processed.append(run_path.name)
            except Exception as exc:
                logger.error(f"Failed to load run {run_path.name}: {exc}")
                # Continue with other runs instead of stopping entirely
                continue

        working_session.commit()
        logger.info(f"Successfully loaded all runs: {stats.to_dict()}")
        return stats.to_dict()
    except Exception as exc:
        logger.error(f"Error loading runs from {base_runs_dir}: {exc}")
        working_session.rollback()
        raise
    finally:
        cleanup()
