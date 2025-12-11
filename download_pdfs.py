"""Standalone PDF downloader - Downloads documents from scraped V1 JSON files.

This script:
1. Reads V1 JSON files from a run directory
2. Extracts document URLs from each project
3. Downloads PDFs using the improved download logic
4. Saves to preview folders with proper field_key naming
5. Creates/updates metadata.json for tracking

Usage:
    python download_pdfs.py --run-dir outputs/raipur-20/runs/run_20251210_090333_f88ae6
    python download_pdfs.py --run-dir outputs/raipur-20/runs/run_20251210_090333_f88ae6 --project CG_PCGRERA250518000012
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List
from urllib.parse import urljoin
import time

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️  WARNING: requests library not installed. Install with: pip install requests")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)


def get_base_url() -> str:
    """Get base URL for resolving relative document URLs."""
    # CG RERA detail page base URL
    return "https://rera.cgstate.gov.in/Project/ViewProjectDetail"


def resolve_url(relative_url: str, base_url: str) -> str:
    """Resolve relative URL to absolute URL."""
    if relative_url.startswith("http"):
        return relative_url
    
    # Handle relative paths like ../Content/ProjectDocuments/...
    return urljoin(base_url, relative_url)


def sanitize_filename(field_key: str, extension: str = ".pdf") -> str:
    """Create safe filename from field_key."""
    # Remove special characters, replace spaces with underscores
    safe_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in field_key)
    return f"{safe_name}{extension}"


def download_document(url: str, output_path: Path, field_key: str, base_url: str) -> Dict:
    """Download a single document with verification.
    
    Returns:
        Dict with keys: success, file_path, file_size, error
    """
    result = {
        "success": False,
        "file_path": None,
        "file_size": 0,
        "error": None
    }
    
    if not HAS_REQUESTS:
        result["error"] = "requests library not available"
        return result
    
    try:
        # Resolve relative URL
        download_url = resolve_url(url, base_url)
        
        LOGGER.info(f"[DOWNLOAD] {field_key}: {download_url}")
        
        # Download with timeout and redirects (disable SSL verification for government sites)
        response = requests.get(download_url, timeout=30, allow_redirects=True, verify=False)
        response.raise_for_status()
        
        content = response.content
        if not content or len(content) == 0:
            raise Exception("Empty response body")
        
        # Determine extension from content-type
        content_type = response.headers.get("content-type", "").lower()
        if "pdf" in content_type:
            extension = ".pdf"
        elif "html" in content_type:
            extension = ".html"
        else:
            extension = ".bin"
        
        # Create filename
        filename = sanitize_filename(field_key, extension)
        file_path = output_path / filename
        
        # Ensure directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Write file
        file_path.write_bytes(content)
        
        # Verify
        if not file_path.exists():
            raise Exception("File not created after write")
        
        actual_size = file_path.stat().st_size
        if actual_size == 0:
            raise Exception("File is empty after write")
        
        result["success"] = True
        result["file_path"] = str(file_path)
        result["file_size"] = actual_size
        
        LOGGER.info(f"[DOWNLOAD_OK] {filename}: {actual_size:,} bytes")
        
    except requests.RequestException as exc:
        error_msg = f"HTTP error: {exc}"
        LOGGER.error(f"[DOWNLOAD_FAIL] {field_key}: {error_msg}")
        result["error"] = error_msg
        
    except Exception as exc:
        error_msg = f"Download failed: {exc}"
        LOGGER.error(f"[DOWNLOAD_FAIL] {field_key}: {error_msg}")
        result["error"] = error_msg
    
    return result


def process_project(v1_json_path: Path, previews_dir: Path, base_url: str) -> Dict:
    """Download all documents for a single project.
    
    Returns:
        Dict with download statistics
    """
    stats = {
        "project_id": None,
        "total_docs": 0,
        "downloaded": 0,
        "failed": 0,
        "skipped": 0,
        "total_bytes": 0,
        "errors": []
    }
    
    try:
        # Load V1 JSON
        with open(v1_json_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # Extract project_id from project_details (correct path)
        project_id = project_data.get("project_details", {}).get("registration_number")
        if not project_id:
            # Fallback: try to extract from filename
            project_id = v1_json_path.stem.replace("project_", "").replace(".v1", "")
        
        stats["project_id"] = project_id
        
        documents = project_data.get("documents", [])
        stats["total_docs"] = len(documents)
        
        if not documents:
            LOGGER.info(f"[SKIP] {project_id}: No documents found")
            return stats
        
        # Create preview directory
        preview_dir = previews_dir / project_id
        preview_dir.mkdir(parents=True, exist_ok=True)
        
        LOGGER.info(f"\n{'='*60}")
        LOGGER.info(f"Processing: {project_id} ({len(documents)} documents)")
        LOGGER.info(f"Output: {preview_dir}")
        LOGGER.info(f"{'='*60}\n")
        
        # Download each document
        download_records = []
        
        for idx, doc in enumerate(documents, 1):
            doc_name = doc.get("name", f"Document_{idx}")
            doc_url = doc.get("url", "")
            doc_type = doc.get("document_type", "Unknown")
            
            # Create unique field_key from document name (sanitized)
            field_key = doc_type if doc_type != "Unknown" else doc_name.replace(" ", "_").replace("/", "_")
            field_key = f"doc_{idx:02d}_{field_key}"  # Prefix with index to ensure uniqueness
            
            # Skip if no URL or invalid URL
            if not doc_url or doc_url in ("NA", "Preview", "Download", "View", "javascript:void(0)"):
                LOGGER.warning(f"[SKIP] {doc_name}: Invalid URL '{doc_url}'")
                stats["skipped"] += 1
                continue
            
            # Download document
            result = download_document(doc_url, preview_dir, field_key, base_url)
            
            if result["success"]:
                stats["downloaded"] += 1
                stats["total_bytes"] += result["file_size"]
            else:
                stats["failed"] += 1
                stats["errors"].append(f"{doc_name}: {result['error']}")
            
            # Record download attempt
            download_records.append({
                "document_name": doc_name,
                "field_key": field_key,
                "source_url": doc_url,
                "file_path": result["file_path"],
                "file_size": result["file_size"],
                "success": result["success"],
                "error": result["error"],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        # Save metadata
        metadata_path = preview_dir / "metadata.json"
        metadata = {
            "project_id": project_id,
            "total_documents": len(documents),
            "downloaded": stats["downloaded"],
            "failed": stats["failed"],
            "skipped": stats["skipped"],
            "total_bytes": stats["total_bytes"],
            "download_records": download_records,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        LOGGER.info(f"\n{'='*60}")
        LOGGER.info(f"✅ {project_id} Complete:")
        LOGGER.info(f"  Downloaded: {stats['downloaded']}/{stats['total_docs']}")
        LOGGER.info(f"  Failed: {stats['failed']}")
        LOGGER.info(f"  Skipped: {stats['skipped']}")
        LOGGER.info(f"  Total size: {stats['total_bytes']:,} bytes ({stats['total_bytes']/1024/1024:.2f} MB)")
        LOGGER.info(f"{'='*60}\n")
        
    except Exception as exc:
        LOGGER.error(f"Error processing project: {exc}")
        stats["errors"].append(f"Project processing error: {exc}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Download PDFs from scraped V1 JSON files")
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Path to run directory (e.g., outputs/raipur-20/runs/run_20251210_090333_f88ae6)"
    )
    parser.add_argument(
        "--project",
        type=str,
        help="Download only specific project ID (e.g., CG_PCGRERA250518000012)"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="https://rera.cgstate.gov.in/Project/ViewProjectDetail",
        help="Base URL for resolving relative document URLs"
    )
    
    args = parser.parse_args()
    
    if not HAS_REQUESTS:
        LOGGER.error("❌ requests library is required. Install with: pip install requests")
        return 1
    
    # Validate run directory
    run_dir = args.run_dir
    if not run_dir.exists():
        LOGGER.error(f"❌ Run directory not found: {run_dir}")
        return 1
    
    scraped_json_dir = run_dir / "scraped_json"
    if not scraped_json_dir.exists():
        LOGGER.error(f"❌ scraped_json directory not found: {scraped_json_dir}")
        return 1
    
    previews_dir = run_dir / "previews"
    previews_dir.mkdir(parents=True, exist_ok=True)
    
    # Find V1 JSON files
    json_files = list(scraped_json_dir.glob("*.json"))
    
    if not json_files:
        LOGGER.error(f"❌ No JSON files found in: {scraped_json_dir}")
        return 1
    
    # Filter by project if specified
    if args.project:
        json_files = [f for f in json_files if args.project in f.name]
        if not json_files:
            LOGGER.error(f"❌ No JSON file found for project: {args.project}")
            return 1
    
    LOGGER.info(f"\n{'#'*60}")
    LOGGER.info(f"# PDF DOWNLOADER")
    LOGGER.info(f"# Run: {run_dir.name}")
    LOGGER.info(f"# Projects: {len(json_files)}")
    LOGGER.info(f"{'#'*60}\n")
    
    # Process each project
    all_stats = []
    
    for json_file in json_files:
        stats = process_project(json_file, previews_dir, args.base_url)
        all_stats.append(stats)
    
    # Summary
    total_docs = sum(s["total_docs"] for s in all_stats)
    total_downloaded = sum(s["downloaded"] for s in all_stats)
    total_failed = sum(s["failed"] for s in all_stats)
    total_skipped = sum(s["skipped"] for s in all_stats)
    total_bytes = sum(s["total_bytes"] for s in all_stats)
    
    LOGGER.info(f"\n{'#'*60}")
    LOGGER.info(f"# SUMMARY")
    LOGGER.info(f"{'#'*60}")
    LOGGER.info(f"Projects processed: {len(all_stats)}")
    LOGGER.info(f"Total documents: {total_docs}")
    LOGGER.info(f"Downloaded: {total_downloaded}")
    LOGGER.info(f"Failed: {total_failed}")
    LOGGER.info(f"Skipped: {total_skipped}")
    LOGGER.info(f"Total size: {total_bytes:,} bytes ({total_bytes/1024/1024:.2f} MB)")
    LOGGER.info(f"{'#'*60}\n")
    
    if total_downloaded > 0:
        LOGGER.info(f"✅ SUCCESS - {total_downloaded} PDFs downloaded to: {previews_dir}")
    else:
        LOGGER.warning(f"⚠️  No PDFs downloaded. Check URLs in scraped_json files.")
    
    # Show errors if any
    all_errors = [err for s in all_stats for err in s["errors"]]
    if all_errors:
        LOGGER.warning(f"\n⚠️  Errors encountered ({len(all_errors)}):")
        for err in all_errors[:10]:  # Show first 10
            LOGGER.warning(f"  - {err}")
        if len(all_errors) > 10:
            LOGGER.warning(f"  ... and {len(all_errors) - 10} more")
    
    return 0


if __name__ == "__main__":
    exit(main())
