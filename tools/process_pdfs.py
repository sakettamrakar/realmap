#!/usr/bin/env python3
"""
Process PDFs - CLI tool for processing RERA PDF documents.

This tool processes PDF documents from scraped run directories,
extracting structured data using OCR and LLM.

Usage:
    # Process a single run directory
    python tools/process_pdfs.py --run-dir outputs/parallel-page1/runs/run_001
    
    # Process all runs from a page
    python tools/process_pdfs.py --page 1
    
    # Process multiple pages
    python tools/process_pdfs.py --pages 1,2,3
    
    # Process specific document types only
    python tools/process_pdfs.py --page 1 --doc-types registration_certificate,layout_plan
    
    # Process without LLM (OCR only)
    python tools/process_pdfs.py --page 1 --no-llm
    
    # Save intermediate OCR text files
    python tools/process_pdfs.py --page 1 --save-ocr
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from cg_rera_extractor import (
    PDFProcessor,
    RunProcessingResult,
    OCRConfig,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


def find_run_directories(
    base_dir: Path,
    pages: Optional[List[int]] = None,
) -> List[Path]:
    """
    Find all run directories to process.
    
    Args:
        base_dir: Base outputs directory
        pages: Optional list of page numbers to process
        
    Returns:
        List of run directory paths
    """
    run_dirs = []
    
    if pages:
        # Process specific pages
        for page in pages:
            page_dir = base_dir / f"parallel-page{page}" / "runs"
            if page_dir.exists():
                for run_dir in sorted(page_dir.iterdir()):
                    if run_dir.is_dir() and run_dir.name.startswith("run_"):
                        run_dirs.append(run_dir)
            else:
                logger.warning("Page directory not found: %s", page_dir)
    else:
        # Process all pages
        for page_dir in sorted(base_dir.glob("parallel-page*")):
            runs_dir = page_dir / "runs"
            if runs_dir.exists():
                for run_dir in sorted(runs_dir.iterdir()):
                    if run_dir.is_dir() and run_dir.name.startswith("run_"):
                        run_dirs.append(run_dir)
    
    return run_dirs


def process_runs(
    run_dirs: List[Path],
    doc_types: Optional[List[str]] = None,
    enable_llm: bool = True,
    save_ocr: bool = False,
    dpi: int = 300,
) -> List[RunProcessingResult]:
    """
    Process all run directories.
    
    Args:
        run_dirs: List of run directory paths
        doc_types: Optional list of document types to process
        enable_llm: Whether to use LLM for extraction
        save_ocr: Whether to save intermediate OCR text files
        dpi: DPI for PDF conversion
        
    Returns:
        List of processing results
    """
    # Configure OCR
    ocr_config = OCRConfig(
        dpi=dpi,
        tesseract_lang="eng+hin",
        easyocr_langs=["en", "hi"],
    )
    
    # Initialize processor
    processor = PDFProcessor(
        ocr_config=ocr_config,
        enable_llm=enable_llm,
        save_intermediate=save_ocr,
    )
    
    results = []
    total = len(run_dirs)
    
    for i, run_dir in enumerate(run_dirs, 1):
        logger.info("=" * 60)
        logger.info("Processing run %d/%d: %s", i, total, run_dir.name)
        logger.info("=" * 60)
        
        try:
            result = processor.process_run_directory(run_dir, doc_types=doc_types)
            results.append(result)
            
            # Log result summary
            if result.success:
                logger.info(
                    "✓ Project %s: %d/%d documents processed successfully",
                    result.project_id,
                    result.documents_successful,
                    result.documents_processed,
                )
                if result.output_path:
                    logger.info("  Output: %s", result.output_path)
            else:
                logger.error(
                    "✗ Project %s failed: %s",
                    result.project_id,
                    result.error_message,
                )
        except Exception as e:
            logger.error("Error processing %s: %s", run_dir, e, exc_info=True)
            results.append(RunProcessingResult(
                run_dir=str(run_dir),
                project_id="unknown",
                success=False,
                error_message=str(e),
            ))
    
    return results


def print_summary(results: List[RunProcessingResult]) -> None:
    """Print processing summary."""
    total_runs = len(results)
    successful_runs = sum(1 for r in results if r.success)
    failed_runs = total_runs - successful_runs
    
    total_docs = sum(r.documents_processed for r in results)
    successful_docs = sum(r.documents_successful for r in results)
    failed_docs = sum(r.documents_failed for r in results)
    
    total_time = sum(r.total_processing_time_ms for r in results)
    
    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)
    print(f"\nRun Directories:")
    print(f"  Total:      {total_runs}")
    print(f"  Successful: {successful_runs}")
    print(f"  Failed:     {failed_runs}")
    
    print(f"\nDocuments:")
    print(f"  Total:      {total_docs}")
    print(f"  Successful: {successful_docs}")
    print(f"  Failed:     {failed_docs}")
    
    print(f"\nTiming:")
    print(f"  Total Time: {total_time / 1000:.1f}s")
    if total_docs > 0:
        print(f"  Avg/Doc:    {total_time / total_docs:.0f}ms")
    
    # List failed runs
    if failed_runs > 0:
        print(f"\nFailed Runs:")
        for r in results:
            if not r.success:
                print(f"  - {r.run_dir}: {r.error_message}")
    
    print("=" * 60)


def save_results_json(
    results: List[RunProcessingResult],
    output_path: Path,
) -> None:
    """Save processing results to JSON file."""
    data = {
        "processed_at": datetime.now().isoformat(),
        "total_runs": len(results),
        "successful_runs": sum(1 for r in results if r.success),
        "results": [
            {
                "run_dir": r.run_dir,
                "project_id": r.project_id,
                "success": r.success,
                "documents_processed": r.documents_processed,
                "documents_successful": r.documents_successful,
                "documents_failed": r.documents_failed,
                "processing_time_ms": r.total_processing_time_ms,
                "output_path": r.output_path,
                "error_message": r.error_message,
            }
            for r in results
        ],
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    logger.info("Results saved to: %s", output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Process RERA PDF documents using OCR and LLM extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--run-dir",
        type=str,
        help="Process a specific run directory",
    )
    input_group.add_argument(
        "--page",
        type=int,
        help="Process all runs from a specific page number",
    )
    input_group.add_argument(
        "--pages",
        type=str,
        help="Process runs from multiple pages (comma-separated, e.g., 1,2,3)",
    )
    input_group.add_argument(
        "--all",
        action="store_true",
        help="Process all available run directories",
    )
    
    # Processing options
    parser.add_argument(
        "--doc-types",
        type=str,
        help="Document types to process (comma-separated)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM extraction (OCR only)",
    )
    parser.add_argument(
        "--save-ocr",
        action="store_true",
        help="Save intermediate OCR text files",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI for PDF conversion (default: 300)",
    )
    
    # Output options
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Base output directory (default: outputs)",
    )
    parser.add_argument(
        "--results-json",
        type=str,
        help="Save processing results to JSON file",
    )
    
    # Logging options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-error output",
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    # Determine base directory
    base_dir = Path(args.output_dir)
    if not base_dir.exists():
        logger.error("Output directory not found: %s", base_dir)
        sys.exit(1)
    
    # Find run directories to process
    if args.run_dir:
        run_dirs = [Path(args.run_dir)]
        if not run_dirs[0].exists():
            logger.error("Run directory not found: %s", args.run_dir)
            sys.exit(1)
    elif args.page:
        run_dirs = find_run_directories(base_dir, pages=[args.page])
    elif args.pages:
        pages = [int(p.strip()) for p in args.pages.split(",")]
        run_dirs = find_run_directories(base_dir, pages=pages)
    else:  # --all
        run_dirs = find_run_directories(base_dir)
    
    if not run_dirs:
        logger.error("No run directories found")
        sys.exit(1)
    
    logger.info("Found %d run directories to process", len(run_dirs))
    
    # Parse document types
    doc_types = None
    if args.doc_types:
        doc_types = [t.strip() for t in args.doc_types.split(",")]
    
    # Process runs
    results = process_runs(
        run_dirs=run_dirs,
        doc_types=doc_types,
        enable_llm=not args.no_llm,
        save_ocr=args.save_ocr,
        dpi=args.dpi,
    )
    
    # Print summary
    print_summary(results)
    
    # Save results JSON if requested
    if args.results_json:
        save_results_json(results, Path(args.results_json))
    
    # Exit with appropriate code
    failed = sum(1 for r in results if not r.success)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
