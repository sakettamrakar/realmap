"""
PDF Extraction Integration Script.

Links downloaded PDFs to V1 JSON documents and updates them with extraction results.

Features:
1. Uses document_name from metadata.json as source of truth for document type
2. Links extracted PDF data back to V1 JSON document records
3. Validates extraction confidence before updating
4. Optionally uses LLM for quality checks on uncertain extractions

Usage:
    python integrate_pdf_extractions.py <run_dir> [--project-id RERA_NUMBER]
    
Example:
    python integrate_pdf_extractions.py outputs/raipur-20/runs/run_20251210_090333_f88ae6 --project-id PCGRERA250518000012
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ai.features.pdf_processing import (
    PDFOrchestrator,
    ProcessingMode,
    TextExtractor,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DocumentLink:
    """Links a downloaded PDF to its V1 JSON document record."""
    document_name: str           # From metadata.json (e.g., "Registration Certificate")
    document_index: int          # Index in V1 JSON documents array
    source_url: str              # Original URL
    local_path: Optional[str]    # Downloaded file path
    file_size: int               # File size in bytes
    download_success: bool       # Whether download succeeded


@dataclass 
class ExtractionUpdate:
    """Update to be applied to a V1 JSON document."""
    document_index: int
    document_name: str
    updates: Dict[str, Any]
    confidence: float
    source: str                  # "text_extraction" or "llm_extraction"
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# DOCUMENT TYPE MAPPING
# =============================================================================

# Map document names to standardized types
DOCUMENT_TYPE_MAP = {
    # Certificates
    "registration certificate": "registration_certificate",
    "colonizer registration certiticate": "colonizer_certificate",
    "ca certificate": "ca_certificate",
    "engineer certificate": "engineer_certificate",
    "encumbrances on land/non-encumbrances certificate": "encumbrance_certificate",
    
    # Financial
    "bank account passbook front page": "bank_passbook",
    "fee calculation sheet": "fee_calculation",
    
    # Legal
    "search report": "search_report",
    "affidavit cum declaration": "affidavit",
    "self declaration by the promoter": "self_declaration",
    "undertaking by the promoter": "undertaking",
    
    # Plans & Approvals  
    "approval letter of town and country planning": "town_planning_approval",
    "sanctioned layout plan": "layout_plan",
    "sanctioned building plan": "building_plan",
    "modified layout plan": "modified_layout_plan",
    "building permission from local authority": "building_permission",
    
    # Clearances
    "environment clearance": "environment_clearance",
    "enviornment clearance": "environment_clearance",  # typo in source
    "nazul clearance": "nazul_clearance",
    "diversion order": "diversion_order",
    
    # Project Details
    "project specifications": "project_specifications",
    "brief details of current project": "project_details",
    "common area facilities": "common_facilities",
    "development team details": "development_team",
    "development work plan": "development_plan",
    "development permission": "development_permission",
    
    # Property
    "apartment details": "apartment_details",
    "garage details": "garage_details",
    "stilt basement parking": "parking_details",
    "open parking": "parking_details",
    "demarcation of land": "land_demarcation",
    "agent details": "agent_details",
}


def normalize_document_type(document_name: str) -> str:
    """Convert document name to standardized type."""
    name_lower = document_name.lower().strip()
    
    # Try exact match first
    if name_lower in DOCUMENT_TYPE_MAP:
        return DOCUMENT_TYPE_MAP[name_lower]
    
    # Try partial match
    for key, doc_type in DOCUMENT_TYPE_MAP.items():
        if key in name_lower or name_lower in key:
            return doc_type
    
    # Fallback to slugified name
    return name_lower.replace(" ", "_").replace("/", "_").replace("-", "_")[:50]


# =============================================================================
# CONFIDENCE THRESHOLDS
# =============================================================================

# Minimum confidence to update V1 JSON
MIN_CONFIDENCE_FOR_UPDATE = 0.3

# Confidence thresholds for different fields
FIELD_CONFIDENCE_THRESHOLDS = {
    "extracted_text": 0.0,        # Always include if we have any text
    "document_type": 0.3,         # Low - we use label anyway
    "approval_number": 0.5,       # Medium - important field
    "approval_date": 0.5,         # Medium - important field
    "amounts": 0.6,               # Higher - financial data needs accuracy
    "areas": 0.6,                 # Higher - measurement data needs accuracy
}


def calculate_extraction_confidence(result, use_llm: bool = False) -> float:
    """
    Calculate confidence score for an extraction result.
    
    LLM extractions get a base confidence boost since they're more reliable.
    """
    if not result.success:
        return 0.0
    
    score = 0.0
    
    # Base score for successful extraction
    score += 0.1
    
    # LLM extraction bonus (more reliable classification)
    if use_llm and result.document_type_confidence >= 0.8:
        score += 0.2
    
    # Text length factor (0-0.2)
    if result.text_length > 1000:
        score += 0.2
    elif result.text_length > 500:
        score += 0.15
    elif result.text_length > 100:
        score += 0.1
    elif result.text_length > 0:
        score += 0.05
    
    # Document type confidence (0-0.25)
    if result.document_type_confidence:
        score += min(result.document_type_confidence, 1.0) * 0.25
    
    # Metadata extraction quality (0-0.35)
    if result.metadata:
        metadata_score = 0.0
        if result.metadata.dates:
            metadata_score += 0.1
        if result.metadata.approval_number:
            metadata_score += 0.15
        if result.metadata.amounts:
            metadata_score += 0.1
        if result.metadata.reference_numbers:
            metadata_score += 0.05
        if result.metadata.summary:
            metadata_score += 0.05
        score += min(metadata_score, 0.35)
    
    return min(score, 1.0)


# =============================================================================
# MAIN INTEGRATION CLASS
# =============================================================================

class PDFExtractionIntegrator:
    """
    Integrates PDF extractions with V1 JSON documents.
    
    By default, uses LLM extraction when GPU is available for better quality.
    Falls back to text-only extraction if GPU is not available.
    """
    
    def __init__(self, run_dir: Path, use_llm: bool = True):
        """
        Initialize integrator.
        
        Args:
            run_dir: Path to the run directory
            use_llm: Whether to use LLM for extraction (default: True)
        """
        self.run_dir = Path(run_dir)
        self.use_llm = use_llm
        self.scraped_json_dir = self.run_dir / "scraped_json"
        self.previews_dir = self.run_dir / "previews"
        
        # Check GPU availability for LLM
        self._gpu_available = self._check_gpu_available()
        
        # Initialize extractor based on mode
        if self.use_llm and self._gpu_available:
            from ai.features.pdf_processing import LLMExtractor
            self.extractor = LLMExtractor(max_pages=10, max_tokens=256)
            logger.info("Using LLM extractor with GPU acceleration")
        else:
            self.extractor = TextExtractor(max_pages=20)
            if self.use_llm and not self._gpu_available:
                logger.warning("LLM requested but GPU not available - using text extraction")
            else:
                logger.info("Using text-only extractor")
    
    def _check_gpu_available(self) -> bool:
        """Check if GPU is available for LLM."""
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0 and len(result.stdout.strip()) > 0
        except Exception:
            return False
    
    def load_v1_json(self, project_id: str) -> dict:
        """Load V1 JSON for a project."""
        v1_path = self.scraped_json_dir / f"project_{project_id}.v1.json"
        if not v1_path.exists():
            raise FileNotFoundError(f"V1 JSON not found: {v1_path}")
        
        with open(v1_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_v1_json(self, project_id: str, data: dict) -> Path:
        """Save updated V1 JSON."""
        v1_path = self.scraped_json_dir / f"project_{project_id}.v1.json"
        
        # Backup original
        backup_path = self.scraped_json_dir / f"project_{project_id}.v1.backup.json"
        if v1_path.exists() and not backup_path.exists():
            import shutil
            shutil.copy(v1_path, backup_path)
            logger.info(f"Backed up original to {backup_path}")
        
        with open(v1_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved updated V1 JSON: {v1_path}")
        return v1_path
    
    def load_download_metadata(self, project_id: str) -> dict:
        """Load download metadata for a project."""
        metadata_path = self.previews_dir / project_id / "metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Download metadata not found: {metadata_path}")
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def build_document_links(
        self,
        v1_data: dict,
        download_metadata: dict
    ) -> List[DocumentLink]:
        """
        Build links between V1 JSON documents and downloaded PDFs.
        """
        links = []
        v1_documents = v1_data.get("documents", [])
        download_records = download_metadata.get("download_records", [])
        
        # Create lookup by document name
        download_by_name = {
            rec["document_name"]: rec for rec in download_records
        }
        
        for idx, doc in enumerate(v1_documents):
            doc_name = doc.get("name", "")
            
            # Find matching download record
            download_rec = download_by_name.get(doc_name)
            
            if download_rec:
                links.append(DocumentLink(
                    document_name=doc_name,
                    document_index=idx,
                    source_url=download_rec.get("source_url", ""),
                    local_path=download_rec.get("file_path"),
                    file_size=download_rec.get("file_size", 0),
                    download_success=download_rec.get("success", False)
                ))
            else:
                # Document exists in V1 but wasn't downloaded (no URL or javascript:void)
                links.append(DocumentLink(
                    document_name=doc_name,
                    document_index=idx,
                    source_url=doc.get("url", ""),
                    local_path=None,
                    file_size=0,
                    download_success=False
                ))
        
        return links
    
    def extract_and_link(
        self,
        link: DocumentLink,
        project_root: Path
    ) -> Optional[ExtractionUpdate]:
        """
        Extract data from a linked PDF and prepare update.
        """
        if not link.download_success or not link.local_path:
            return None
        
        # Resolve full path
        pdf_path = project_root / link.local_path
        if not pdf_path.exists():
            logger.warning(f"PDF not found: {pdf_path}")
            return None
        
        # Extract using configured extractor (LLM or text-only)
        result = self.extractor.process(pdf_path)
        
        if not result.success:
            logger.warning(f"Extraction failed for {link.document_name}: {result.error}")
            return None
        
        # Calculate confidence (with LLM boost if applicable)
        is_llm = self.use_llm and self._gpu_available
        confidence = calculate_extraction_confidence(result, use_llm=is_llm)
        
        # Determine extraction source
        source = "llm_extraction" if is_llm else "text_extraction"
        
        # Prepare updates
        updates = {
            # Use the label as document type (source of truth)
            "document_type": normalize_document_type(link.document_name),
            "local_file_path": link.local_path,
            "file_size_bytes": link.file_size,
            # Add extraction source for traceability
            "extraction_source": source,
        }
        
        warnings = []
        
        # Add extraction data based on confidence
        if result.text_length > 0:
            updates["extracted_text_length"] = result.text_length
            updates["page_count"] = result.page_count
        else:
            warnings.append("No text extracted - may be scanned/image PDF")
        
        if result.metadata:
            if result.metadata.approval_number and confidence >= FIELD_CONFIDENCE_THRESHOLDS["approval_number"]:
                updates["approval_number"] = result.metadata.approval_number
            
            if result.metadata.approval_date and confidence >= FIELD_CONFIDENCE_THRESHOLDS["approval_date"]:
                updates["approval_date"] = result.metadata.approval_date
            
            if result.metadata.dates:
                updates["dates_found"] = result.metadata.dates[:5]  # Limit to 5
            
            if result.metadata.amounts and confidence >= FIELD_CONFIDENCE_THRESHOLDS["amounts"]:
                updates["amounts_found"] = result.metadata.amounts[:5]
            
            if result.metadata.reference_numbers:
                updates["reference_numbers"] = result.metadata.reference_numbers[:5]
        
        # Add processing metadata
        updates["extraction_metadata"] = {
            "processor": result.processor_name,
            "processor_version": result.processor_version,
            "processing_time_ms": result.processing_time_ms,
            "confidence": round(confidence, 3),
            "extracted_at": datetime.now().isoformat(),
        }
        
        return ExtractionUpdate(
            document_index=link.document_index,
            document_name=link.document_name,
            updates=updates,
            confidence=confidence,
            source="text_extraction",
            warnings=warnings + (result.warnings or [])
        )
    
    def apply_updates(
        self,
        v1_data: dict,
        updates: List[ExtractionUpdate],
        min_confidence: float = MIN_CONFIDENCE_FOR_UPDATE
    ) -> dict:
        """
        Apply extraction updates to V1 JSON data.
        """
        documents = v1_data.get("documents", [])
        applied_count = 0
        skipped_count = 0
        
        for update in updates:
            if update.confidence < min_confidence:
                logger.debug(
                    f"Skipping {update.document_name} - confidence {update.confidence:.2f} "
                    f"below threshold {min_confidence}"
                )
                skipped_count += 1
                continue
            
            if update.document_index < len(documents):
                doc = documents[update.document_index]
                
                # Apply updates
                for key, value in update.updates.items():
                    doc[key] = value
                
                # Add warnings if any
                if update.warnings:
                    doc["extraction_warnings"] = update.warnings
                
                applied_count += 1
                logger.info(
                    f"Updated {update.document_name} (confidence: {update.confidence:.2f})"
                )
        
        logger.info(f"Applied {applied_count} updates, skipped {skipped_count}")
        
        # Add integration metadata
        if "extraction_metadata" not in v1_data:
            v1_data["extraction_metadata"] = {}
        
        v1_data["extraction_metadata"]["last_extraction"] = {
            "timestamp": datetime.now().isoformat(),
            "documents_updated": applied_count,
            "documents_skipped": skipped_count,
            "min_confidence_threshold": min_confidence,
        }
        
        return v1_data
    
    def process_project(
        self,
        project_id: str,
        dry_run: bool = False,
        min_confidence: float = MIN_CONFIDENCE_FOR_UPDATE
    ) -> dict:
        """
        Process all PDFs for a project and update V1 JSON.
        
        Args:
            project_id: RERA registration number
            dry_run: If True, don't save changes
            min_confidence: Minimum confidence to apply updates
            
        Returns:
            Summary of processing
        """
        # The file_path in metadata.json is relative to realmap root
        # We need to find the project root by going up from run_dir
        # run_dir example: outputs/raipur-20/runs/run_20251210_090333_f88ae6
        # project root is the parent that contains the 'outputs' folder
        project_root = self.run_dir
        while project_root.name != "realmap" and project_root.parent != project_root:
            if (project_root / "outputs").exists():
                break
            project_root = project_root.parent
        
        # If we couldn't find it, use CWD
        if not (project_root / "outputs").exists():
            project_root = Path.cwd()
        
        logger.info(f"Processing project: {project_id}")
        logger.info(f"Run directory: {self.run_dir}")
        
        # Load data
        v1_data = self.load_v1_json(project_id)
        download_metadata = self.load_download_metadata(project_id)
        
        # Build links
        links = self.build_document_links(v1_data, download_metadata)
        logger.info(f"Found {len(links)} document links")
        
        # Process each linked PDF
        updates = []
        for link in links:
            if link.download_success and link.local_path:
                update = self.extract_and_link(link, project_root)
                if update:
                    updates.append(update)
        
        logger.info(f"Generated {len(updates)} extraction updates")
        
        # Apply updates
        if updates:
            v1_data = self.apply_updates(v1_data, updates, min_confidence)
        
        # Save if not dry run
        if not dry_run:
            self.save_v1_json(project_id, v1_data)
        else:
            logger.info("Dry run - changes not saved")
        
        # Return summary
        return {
            "project_id": project_id,
            "total_documents": len(v1_data.get("documents", [])),
            "downloaded_pdfs": len([l for l in links if l.download_success]),
            "extractions_generated": len(updates),
            "extractions_applied": len([u for u in updates if u.confidence >= min_confidence]),
            "dry_run": dry_run,
        }


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Integrate PDF extractions with V1 JSON"
    )
    parser.add_argument(
        "run_dir",
        help="Path to the run directory"
    )
    parser.add_argument(
        "--project-id", "-p",
        help="RERA registration number (if not specified, processes all)"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Don't save changes, just show what would be done"
    )
    parser.add_argument(
        "--min-confidence", "-c",
        type=float,
        default=MIN_CONFIDENCE_FOR_UPDATE,
        help=f"Minimum confidence threshold (default: {MIN_CONFIDENCE_FOR_UPDATE})"
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM extraction (use text-only mode)"
    )
    
    args = parser.parse_args()
    
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        logger.error(f"Run directory not found: {run_dir}")
        return 1
    
    # Default to LLM mode, use --no-llm to disable
    use_llm = not args.no_llm
    integrator = PDFExtractionIntegrator(run_dir, use_llm=use_llm)
    
    if args.project_id:
        # Process single project
        try:
            summary = integrator.process_project(
                args.project_id,
                dry_run=args.dry_run,
                min_confidence=args.min_confidence
            )
            print("\n" + "=" * 50)
            print("PROCESSING SUMMARY")
            print("=" * 50)
            for key, value in summary.items():
                print(f"  {key}: {value}")
        except Exception as e:
            logger.error(f"Failed to process {args.project_id}: {e}")
            return 1
    else:
        # Process all projects in previews directory
        previews_dir = run_dir / "previews"
        if not previews_dir.exists():
            logger.error(f"Previews directory not found: {previews_dir}")
            return 1
        
        project_dirs = [d for d in previews_dir.iterdir() if d.is_dir()]
        logger.info(f"Found {len(project_dirs)} projects to process")
        
        for project_dir in project_dirs:
            project_id = project_dir.name
            try:
                summary = integrator.process_project(
                    project_id,
                    dry_run=args.dry_run,
                    min_confidence=args.min_confidence
                )
                print(f"\n{project_id}: {summary['extractions_applied']} updates applied")
            except Exception as e:
                logger.error(f"Failed to process {project_id}: {e}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
