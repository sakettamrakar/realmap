"""Regenerate V1 JSON files from raw_extracted with fixed mapper.

This script:
1. Reads raw_extracted JSON files
2. Re-applies the FIXED mapper logic (uses field.links[0])
3. Regenerates V1 JSON files with correct URLs
4. Preserves original files with .backup extension

Usage:
    python regenerate_v1_json.py --run-dir outputs/raipur-20/runs/run_20251210_090333_f88ae6
    python regenerate_v1_json.py --run-dir outputs/raipur-20/runs/run_20251210_090333_f88ae6 --project CG_PCGRERA250518000012
"""

import argparse
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List

from cg_rera_extractor.parsing.mapper import map_raw_to_v1
from cg_rera_extractor.parsing.schema import RawExtractedProject

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)


def regenerate_project(raw_json_path: Path, scraped_json_dir: Path, backup: bool = True) -> Dict:
    """Regenerate V1 JSON for a single project.
    
    Returns:
        Dict with statistics: urls_fixed, total_docs, etc.
    """
    stats = {
        "project_id": None,
        "total_docs": 0,
        "urls_fixed": 0,
        "urls_still_invalid": 0,
        "success": False
    }
    
    try:
        # Load raw extracted data
        with open(raw_json_path, 'r', encoding='utf-8') as f:
            raw_data_dict = json.load(f)
        
        # Parse as RawExtractedProject
        raw_data = RawExtractedProject(**raw_data_dict)
        
        # Apply fixed mapper
        v1_project = map_raw_to_v1(raw_data)
        
        project_id = v1_project.project_details.registration_number or "UNKNOWN"
        stats["project_id"] = project_id
        stats["total_docs"] = len(v1_project.documents)
        
        # Count fixed URLs
        for doc in v1_project.documents:
            if doc.url and doc.url not in ("NA", "Preview", "Download", "View", "javascript:void(0)"):
                stats["urls_fixed"] += 1
            else:
                stats["urls_still_invalid"] += 1
        
        # Generate output path - match original filename pattern from raw_json_path
        output_filename = raw_json_path.name.replace('.json', '.v1.json')
        output_path = scraped_json_dir / output_filename
        
        # Backup existing file
        if backup and output_path.exists():
            backup_path = output_path.with_suffix('.json.backup')
            shutil.copy2(output_path, backup_path)
            LOGGER.debug(f"Backed up: {backup_path.name}")
        
        # Write new V1 JSON
        scraped_json_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"DEBUG: Writing to: {output_path}")
        print(f"DEBUG: File exists before write: {output_path.exists()}")
        print(f"DEBUG: First URL in v1_project: {v1_project.documents[0].url if v1_project.documents else 'NO DOCS'}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(v1_project.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"DEBUG: File exists after write: {output_path.exists()}")
        print(f"DEBUG: File size: {output_path.stat().st_size if output_path.exists() else 0}")
        
        stats["success"] = True
        
        LOGGER.info(
            f"✅ {project_id}: {stats['urls_fixed']}/{stats['total_docs']} URLs fixed "
            f"({stats['urls_still_invalid']} still invalid)"
        )
        
    except Exception as exc:
        LOGGER.error(f"❌ Failed to regenerate {raw_json_path.name}: {exc}")
        stats["success"] = False
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Regenerate V1 JSON files with fixed mapper")
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Path to run directory"
    )
    parser.add_argument(
        "--project",
        type=str,
        help="Regenerate only specific project ID"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't create backup files"
    )
    
    args = parser.parse_args()
    
    # Validate directories
    run_dir = args.run_dir
    if not run_dir.exists():
        LOGGER.error(f"❌ Run directory not found: {run_dir}")
        return 1
    
    raw_extracted_dir = run_dir / "raw_extracted"
    if not raw_extracted_dir.exists():
        LOGGER.error(f"❌ raw_extracted directory not found: {raw_extracted_dir}")
        return 1
    
    scraped_json_dir = run_dir / "scraped_json"
    
    # Find raw JSON files
    json_files = list(raw_extracted_dir.glob("*.json"))
    
    if not json_files:
        LOGGER.error(f"❌ No JSON files found in: {raw_extracted_dir}")
        return 1
    
    # Filter by project if specified
    if args.project:
        json_files = [f for f in json_files if args.project in f.name]
        if not json_files:
            LOGGER.error(f"❌ No JSON file found for project: {args.project}")
            return 1
    
    LOGGER.info(f"\n{'#'*60}")
    LOGGER.info(f"# V1 JSON REGENERATOR")
    LOGGER.info(f"# Run: {run_dir.name}")
    LOGGER.info(f"# Projects: {len(json_files)}")
    LOGGER.info(f"# Backup: {not args.no_backup}")
    LOGGER.info(f"{'#'*60}\n")
    
    # Regenerate each project
    all_stats = []
    
    for json_file in json_files:
        stats = regenerate_project(json_file, scraped_json_dir, backup=not args.no_backup)
        all_stats.append(stats)
    
    # Summary
    successful = sum(1 for s in all_stats if s["success"])
    total_docs = sum(s["total_docs"] for s in all_stats)
    total_fixed = sum(s["urls_fixed"] for s in all_stats)
    total_invalid = sum(s["urls_still_invalid"] for s in all_stats)
    
    LOGGER.info(f"\n{'#'*60}")
    LOGGER.info(f"# SUMMARY")
    LOGGER.info(f"{'#'*60}")
    LOGGER.info(f"Projects regenerated: {successful}/{len(all_stats)}")
    LOGGER.info(f"Total documents: {total_docs}")
    LOGGER.info(f"URLs fixed: {total_fixed}")
    LOGGER.info(f"URLs still invalid: {total_invalid}")
    LOGGER.info(f"Success rate: {total_fixed/total_docs*100:.1f}%" if total_docs > 0 else "N/A")
    LOGGER.info(f"{'#'*60}\n")
    
    if total_fixed > 0:
        LOGGER.info(f"✅ SUCCESS - Regenerated V1 JSON files in: {scraped_json_dir}")
        LOGGER.info(f"\nNext step: Run PDF downloader:")
        LOGGER.info(f"  python download_pdfs.py --run-dir {run_dir}")
    else:
        LOGGER.warning(f"⚠️  No URLs were fixed. Check mapper.py implementation.")
    
    return 0


if __name__ == "__main__":
    exit(main())
