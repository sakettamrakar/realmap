"""
Data Merger for Enrichment

Merges PDF-extracted data with scraped metadata to create
comprehensive enriched project records.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .conflict_resolver import ConflictResolver, ConflictResolution, ResolutionStrategy

logger = logging.getLogger(__name__)


@dataclass
class MergeResult:
    """Result of data merge operation"""
    success: bool
    project_id: str
    original_data: Dict[str, Any]
    enriched_data: Dict[str, Any]
    pdf_extractions: List[Dict[str, Any]]
    resolutions: Dict[str, ConflictResolution]
    fields_added: List[str]
    fields_updated: List[str]
    conflicts_detected: int
    needs_review: bool
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "project_id": self.project_id,
            "enriched_data": self.enriched_data,
            "pdf_extractions": self.pdf_extractions,
            "fields_added": self.fields_added,
            "fields_updated": self.fields_updated,
            "conflicts_detected": self.conflicts_detected,
            "needs_review": self.needs_review,
            "errors": self.errors,
            "merge_timestamp": datetime.now().isoformat(),
        }


class DataMerger:
    """
    Merge PDF-extracted data with scraped metadata.
    
    Creates enriched V2 JSON files that combine:
    - Original scraped data (from RERA website)
    - PDF-extracted data (from downloaded documents)
    - Data source tracking
    - Conflict resolution notes
    
    Usage:
        merger = DataMerger()
        result = merger.merge_project(scraped_json, pdf_extractions)
        enriched = result.enriched_data
    """
    
    # Mapping from PDF extraction fields to V1 JSON fields
    FIELD_MAPPING = {
        # Registration Certificate -> project_details
        "registration_number": "project_details.registration_number",
        "registration_date": "project_details.registration_date",
        "valid_till": "project_details.expected_completion_date",
        "project_name": "project_details.project_name",
        "project_type": "project_details.project_type",
        "project_address": "project_details.project_address",
        "project_district": "project_details.district",
        "project_tehsil": "project_details.tehsil",
        "total_land_area": "project_details.total_land_area",
        "total_units": "project_details.total_units",
        
        # Bank Passbook -> bank_details
        "bank_name": "bank_details.0.bank_name",
        "branch_name": "bank_details.0.branch_name",
        "account_number": "bank_details.0.account_number",
        "ifsc_code": "bank_details.0.ifsc_code",
        
        # Promoter -> promoter_details
        "promoter_name": "promoter_details.0.name",
        "promoter_type": "promoter_details.0.organisation_type",
        "promoter_address": "promoter_details.0.address",
        
        # Layout Plan -> land_details
        "total_plots": "land_details.total_plots",
        "open_space_percentage": "land_details.open_space_percentage",
        "survey_numbers": "land_details.survey_numbers",
    }
    
    def __init__(self, conflict_resolver: Optional[ConflictResolver] = None):
        """
        Initialize data merger.
        
        Args:
            conflict_resolver: Custom conflict resolver (uses default if None)
        """
        self.resolver = conflict_resolver or ConflictResolver()
    
    def merge_project(
        self,
        scraped_data: Dict[str, Any],
        pdf_extractions: List[Dict[str, Any]],
        project_id: Optional[str] = None
    ) -> MergeResult:
        """
        Merge scraped data with PDF extractions.
        
        Args:
            scraped_data: Original V1 JSON from scraping
            pdf_extractions: List of extraction results from PDFs
            project_id: Optional project identifier
            
        Returns:
            MergeResult with enriched data
        """
        errors = []
        fields_added = []
        fields_updated = []
        resolutions = {}
        
        # Get project ID from data if not provided
        if not project_id:
            project_id = scraped_data.get("project_details", {}).get(
                "registration_number", "unknown"
            )
        
        # Start with a copy of scraped data
        enriched = json.loads(json.dumps(scraped_data))
        
        # Update schema version
        if "metadata" not in enriched:
            enriched["metadata"] = {}
        enriched["metadata"]["schema_version"] = "2.0"
        enriched["metadata"]["enriched_at"] = datetime.now().isoformat()
        enriched["metadata"]["data_sources"] = ["scraped"]
        
        # Initialize extracted_documents section
        if "extracted_documents" not in enriched:
            enriched["extracted_documents"] = {}
        
        # Process each PDF extraction
        for extraction in pdf_extractions:
            doc_type = extraction.get("document_type", "unknown")
            
            # Store full extraction in extracted_documents
            enriched["extracted_documents"][doc_type] = extraction
            
            # Update data sources
            if "pdf_extracted" not in enriched["metadata"]["data_sources"]:
                enriched["metadata"]["data_sources"].append("pdf_extracted")
            
            # Merge fields into main structure
            for pdf_field, json_path in self.FIELD_MAPPING.items():
                if pdf_field not in extraction:
                    continue
                
                pdf_value = extraction[pdf_field]
                if pdf_value is None:
                    continue
                
                # Get current value from scraped data
                scraped_value = self._get_nested_value(scraped_data, json_path)
                
                # Resolve conflict if both have values
                if scraped_value is not None and pdf_value != scraped_value:
                    resolution = self.resolver.resolve(pdf_field, scraped_value, pdf_value)
                    resolutions[pdf_field] = resolution
                    final_value = resolution.resolved_value
                    
                    if resolution.resolved_value != scraped_value:
                        fields_updated.append(pdf_field)
                else:
                    final_value = pdf_value
                    if scraped_value is None:
                        fields_added.append(pdf_field)
                
                # Set the value in enriched data
                try:
                    self._set_nested_value(enriched, json_path, final_value)
                except Exception as e:
                    errors.append(f"Failed to set {json_path}: {e}")
        
        # Add data source tracking
        if "field_sources" not in enriched["metadata"]:
            enriched["metadata"]["field_sources"] = {}
        
        for field in fields_added:
            enriched["metadata"]["field_sources"][field] = "pdf_extracted"
        
        for field in fields_updated:
            enriched["metadata"]["field_sources"][field] = "pdf_extracted (updated)"
        
        # Count conflicts needing review
        conflicts = sum(1 for r in resolutions.values() if r.needs_review)
        
        return MergeResult(
            success=len(errors) == 0,
            project_id=project_id,
            original_data=scraped_data,
            enriched_data=enriched,
            pdf_extractions=pdf_extractions,
            resolutions=resolutions,
            fields_added=fields_added,
            fields_updated=fields_updated,
            conflicts_detected=conflicts,
            needs_review=conflicts > 0,
            errors=errors
        )
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        parts = path.split(".")
        current = data
        
        for part in parts:
            if current is None:
                return None
            
            # Handle array index
            if part.isdigit():
                idx = int(part)
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    return None
            else:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
        
        return current
    
    def _set_nested_value(self, data: Dict, path: str, value: Any):
        """Set value in nested dictionary using dot notation"""
        parts = path.split(".")
        current = data
        
        for i, part in enumerate(parts[:-1]):
            # Handle array index
            if part.isdigit():
                idx = int(part)
                if isinstance(current, list):
                    while len(current) <= idx:
                        current.append({})
                    current = current[idx]
                else:
                    raise ValueError(f"Expected list at {'.'.join(parts[:i])}")
            else:
                if part not in current:
                    # Check if next part is array index
                    next_part = parts[i + 1]
                    current[part] = [] if next_part.isdigit() else {}
                current = current[part]
        
        # Set final value
        final_part = parts[-1]
        if final_part.isdigit():
            idx = int(final_part)
            while len(current) <= idx:
                current.append(None)
            current[idx] = value
        else:
            current[final_part] = value
    
    def merge_and_save(
        self,
        scraped_json_path: str,
        pdf_extractions: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> MergeResult:
        """
        Load scraped JSON, merge with extractions, and save enriched JSON.
        
        Args:
            scraped_json_path: Path to original V1 JSON
            pdf_extractions: Extraction results from PDFs
            output_path: Output path (default: same dir with .enriched.v2.json)
            
        Returns:
            MergeResult
        """
        scraped_path = Path(scraped_json_path)
        
        # Load scraped data
        with open(scraped_path, 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)
        
        # Get project ID from filename
        project_id = scraped_path.stem.replace("project_", "").replace(".v1", "")
        
        # Merge
        result = self.merge_project(scraped_data, pdf_extractions, project_id)
        
        # Determine output path
        if output_path is None:
            output_path = scraped_path.parent / f"{scraped_path.stem.replace('.v1', '')}.enriched.v2.json"
        
        # Save enriched data
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.enriched_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved enriched data to: {output_path}")
        
        return result
    
    def generate_merge_report(self, results: List[MergeResult]) -> Dict[str, Any]:
        """
        Generate summary report for batch merge operation.
        
        Args:
            results: List of MergeResult from batch processing
            
        Returns:
            Summary report dictionary
        """
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        needs_review = [r for r in results if r.needs_review]
        
        total_added = sum(len(r.fields_added) for r in results)
        total_updated = sum(len(r.fields_updated) for r in results)
        total_conflicts = sum(r.conflicts_detected for r in results)
        
        return {
            "total_processed": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "needs_review": len(needs_review),
            "total_fields_added": total_added,
            "total_fields_updated": total_updated,
            "total_conflicts": total_conflicts,
            "failed_projects": [r.project_id for r in failed],
            "review_projects": [r.project_id for r in needs_review],
            "timestamp": datetime.now().isoformat(),
        }
