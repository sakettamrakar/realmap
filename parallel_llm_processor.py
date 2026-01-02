"""Parallel LLM PDF Processor - Processes PDFs with AI extraction in parallel batches.

This script:
1. Finds all runs with downloaded PDFs
2. Processes PDFs in parallel batches for optimal GPU/CPU utilization
3. Provides real-time progress tracking
4. Saves results and integrates with JSON files

Usage:
    python parallel_llm_processor.py --workers 2 --batch-size 10
    python parallel_llm_processor.py --workers 4 --pages 1-10 --mode text_only
    python parallel_llm_processor.py --pages 1-5 --skip-processed
"""

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables for LLM GPU processing
os.environ.setdefault("MODEL_PATH", "C:/models/ai/general/v1/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf")
os.environ.setdefault("GPU_LAYERS", "33")
os.environ.setdefault("AI_ENABLED", "true")
os.environ.setdefault("CONTEXT_SIZE", "4096")
os.environ.setdefault("LLM_TIMEOUT_SEC", "300")  # 5 minutes for complex PDFs
os.environ.setdefault("LLM_ENABLE_SUMMARY", "false")  # Disable summary by default for speed

from ai.features.pdf_processing import (
    PDFOrchestrator,
    ProcessingMode,
    BatchResult,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(threadName)-10s] - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)


class ParallelLLMProcessor:
    """Manages parallel LLM processing of PDFs across multiple runs."""
    
    def __init__(
        self,
        workers: int = 2,
        batch_size: int = 10,
        mode: ProcessingMode = ProcessingMode.TEXT_ONLY
    ):
        self.workers = workers
        self.batch_size = batch_size
        self.mode = mode
        self.stats = {
            'total_runs': 0,
            'total_projects': 0,
            'total_pdfs': 0,
            'processed_pdfs': 0,
            'successful_pdfs': 0,
            'failed_pdfs': 0,
            'start_time': time.time()
        }
    
    def find_runs_with_pdfs(self, pages: Optional[str] = None) -> List[Path]:
        """Find all runs that have PDFs downloaded."""
        outputs_dir = Path("outputs")
        runs = []
        
        if pages:
            # Parse page specification
            if '-' in pages:
                start, end = map(int, pages.split('-'))
                page_nums = range(start, end + 1)
            elif ',' in pages:
                page_nums = map(int, pages.split(','))
            else:
                page_nums = [int(pages)]
            
            # Find specific page directories (both single and combined)
            for page_num in page_nums:
                page_dir = outputs_dir / f"parallel-page{page_num}"
                if page_dir.exists():
                    runs_dir = page_dir / "runs"
                    if runs_dir.exists():
                        runs.extend(runs_dir.glob("run_*"))
        else:
            # Find all parallel page runs (both single pages and combined ranges)
            for page_dir in outputs_dir.glob("parallel-page*"):
                runs_dir = page_dir / "runs"
                if runs_dir.exists():
                    runs.extend(runs_dir.glob("run_*"))
            
            # Also include combined page directories (parallel-pages28-29, etc.)
            for page_dir in outputs_dir.glob("parallel-pages*"):
                runs_dir = page_dir / "runs"
                if runs_dir.exists():
                    runs.extend(runs_dir.glob("run_*"))
        
        # Filter runs that have PDFs
        filtered_runs = []
        for run_dir in runs:
            if not run_dir.is_dir():
                continue
            
            previews_dir = run_dir / "previews"
            if not previews_dir.exists():
                continue
            
            # Check if any project has PDFs
            has_pdfs = False
            for project_dir in previews_dir.glob("*"):
                if project_dir.is_dir() and any(project_dir.glob("*.pdf")):
                    has_pdfs = True
                    break
            
            if has_pdfs:
                filtered_runs.append(run_dir)
        
        return sorted(filtered_runs)
    
    def find_project_pdfs(self, run_dir: Path) -> Dict[str, List[Path]]:
        """Find all PDFs for each project in a run."""
        previews_dir = run_dir / "previews"
        if not previews_dir.exists():
            return {}
        
        project_pdfs = {}
        for project_dir in previews_dir.glob("*"):
            if not project_dir.is_dir():
                continue
            
            pdfs = list(project_dir.glob("*.pdf"))
            if pdfs:
                project_pdfs[project_dir.name] = pdfs
        
        return project_pdfs
    
    def process_project_batch(
        self,
        run_dir: Path,
        project_id: str,
        pdf_files: List[Path]
    ) -> Tuple[bool, str, Dict]:
        """Process PDFs for a single project."""
        try:
            LOGGER.info(f"Processing {project_id}: {len(pdf_files)} PDFs")
            
            # Create orchestrator (no DB session for now)
            orchestrator = PDFOrchestrator(
                text_max_pages=20,
                llm_max_pages=10,
                skip_processed=False
            )
            
            # Process PDFs in the project directory
            project_dir = pdf_files[0].parent
            batch_result = orchestrator.process_directory(
                directory=project_dir,
                mode=self.mode,
                recursive=False,
                max_files=self.batch_size
            )
            
            # Save results
            results_file = project_dir / "pdf_processing_results.json"
            orchestrator.export_results_json(batch_result, results_file)
            
            stats = {
                'total': batch_result.total_files,
                'processed': batch_result.processed,
                'successful': batch_result.successful,
                'failed': batch_result.failed,
                'time_ms': batch_result.processing_time_ms
            }
            
            LOGGER.info(
                f"✅ {project_id}: {stats['successful']}/{stats['processed']} "
                f"in {stats['time_ms']/1000:.1f}s"
            )
            
            return True, project_id, stats
            
        except Exception as e:
            LOGGER.error(f"❌ {project_id}: {e}")
            return False, project_id, {'error': str(e)}
    
    def process_run(
        self,
        run_dir: Path,
        skip_processed: bool = False
    ) -> Tuple[int, int, int]:
        """Process all projects in a run.
        
        Returns:
            (total_projects, successful_projects, total_pdfs_processed)
        """
        run_name = run_dir.name
        LOGGER.info(f"{'='*60}")
        LOGGER.info(f"Processing run: {run_name}")
        LOGGER.info(f"{'='*60}")
        
        # Find projects with PDFs
        project_pdfs = self.find_project_pdfs(run_dir)
        
        if not project_pdfs:
            LOGGER.info(f"No PDFs found in {run_name}")
            return 0, 0, 0
        
        LOGGER.info(f"Found {len(project_pdfs)} projects with PDFs")
        
        total_projects = len(project_pdfs)
        successful_projects = 0
        total_pdfs = 0
        
        # Process each project
        for project_id, pdf_files in project_pdfs.items():
            if skip_processed:
                # Check if already processed
                results_file = pdf_files[0].parent / "pdf_processing_results.json"
                if results_file.exists():
                    LOGGER.info(f"Skipping {project_id} (already processed)")
                    continue
            
            success, _, stats = self.process_project_batch(
                run_dir, project_id, pdf_files
            )
            
            if success:
                successful_projects += 1
                total_pdfs += stats.get('successful', 0)
                self.stats['successful_pdfs'] += stats.get('successful', 0)
                self.stats['failed_pdfs'] += stats.get('failed', 0)
            
            self.stats['processed_pdfs'] += stats.get('processed', 0)
        
        return total_projects, successful_projects, total_pdfs
    
    def process_all(
        self,
        pages: Optional[str] = None,
        skip_processed: bool = False
    ) -> None:
        """Process all runs in parallel."""
        LOGGER.info("="*70)
        LOGGER.info("PARALLEL LLM PDF PROCESSOR")
        LOGGER.info(f"Mode: {self.mode.value}")
        LOGGER.info("="*70)
        
        # Find runs
        LOGGER.info(f"Scanning for runs with PDFs (pages={pages or 'all'})...")
        runs = self.find_runs_with_pdfs(pages)
        
        if not runs:
            LOGGER.info("✅ No runs with PDFs found!")
            return
        
        self.stats['total_runs'] = len(runs)
        
        # Count total PDFs
        for run_dir in runs:
            project_pdfs = self.find_project_pdfs(run_dir)
            self.stats['total_projects'] += len(project_pdfs)
            for pdfs in project_pdfs.values():
                self.stats['total_pdfs'] += len(pdfs)
        
        LOGGER.info(f"Found {len(runs)} runs with PDFs")
        LOGGER.info(f"Total projects: {self.stats['total_projects']}")
        LOGGER.info(f"Total PDFs: {self.stats['total_pdfs']}")
        LOGGER.info(f"Using {self.workers} parallel workers")
        LOGGER.info(f"Batch size: {self.batch_size} PDFs per project")
        LOGGER.info("="*70)
        
        # Process runs in parallel
        completed_runs = 0
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Submit all tasks
            future_to_run = {
                executor.submit(self.process_run, run_dir, skip_processed): run_dir
                for run_dir in runs
            }
            
            # Process completed tasks
            for future in as_completed(future_to_run):
                run_dir = future_to_run[future]
                try:
                    total_proj, success_proj, pdfs_processed = future.result()
                    completed_runs += 1
                    
                    # Progress update
                    LOGGER.info(
                        f"\nProgress: {completed_runs}/{len(runs)} runs | "
                        f"{self.stats['processed_pdfs']}/{self.stats['total_pdfs']} PDFs | "
                        f"Success: {self.stats['successful_pdfs']} | "
                        f"Failed: {self.stats['failed_pdfs']}\n"
                    )
                    
                except Exception as e:
                    LOGGER.error(f"Run {run_dir.name} failed: {e}")
                    completed_runs += 1
        
        # Final summary
        elapsed = time.time() - self.stats['start_time']
        
        LOGGER.info("\n" + "="*70)
        LOGGER.info("PROCESSING COMPLETE")
        LOGGER.info("="*70)
        LOGGER.info(f"Total runs: {self.stats['total_runs']}")
        LOGGER.info(f"Total projects: {self.stats['total_projects']}")
        LOGGER.info(f"Total PDFs: {self.stats['total_pdfs']}")
        LOGGER.info(f"Processed: {self.stats['processed_pdfs']}")
        LOGGER.info(f"Successful: {self.stats['successful_pdfs']}")
        LOGGER.info(f"Failed: {self.stats['failed_pdfs']}")
        
        if self.stats['processed_pdfs'] > 0:
            success_rate = (self.stats['successful_pdfs'] / self.stats['processed_pdfs']) * 100
            LOGGER.info(f"Success rate: {success_rate:.1f}%")
        
        LOGGER.info(f"Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        
        if self.stats['processed_pdfs'] > 0:
            avg_time = elapsed / self.stats['processed_pdfs']
            LOGGER.info(f"Average: {avg_time:.2f}s per PDF")
        
        LOGGER.info("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Process PDFs with LLM in parallel batches"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Number of parallel workers (default: 2, use 1 for GPU processing)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="PDFs to process per project batch (default: 10)"
    )
    parser.add_argument(
        "--pages",
        type=str,
        help="Page range or list (e.g., '1-25' or '1,2,3')"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=['text_only', 'llm_only', 'hybrid', 'auto'],
        default='text_only',
        help="Processing mode (default: text_only for speed)"
    )
    parser.add_argument(
        "--skip-processed",
        action="store_true",
        help="Skip projects that already have results"
    )
    
    args = parser.parse_args()
    
    # Convert mode string to enum
    mode_map = {
        'text_only': ProcessingMode.TEXT_ONLY,
        'llm_only': ProcessingMode.LLM_ONLY,
        'hybrid': ProcessingMode.HYBRID,
        'auto': ProcessingMode.AUTO
    }
    mode = mode_map[args.mode]
    
    processor = ParallelLLMProcessor(
        workers=args.workers,
        batch_size=args.batch_size,
        mode=mode
    )
    processor.process_all(pages=args.pages, skip_processed=args.skip_processed)
    
    return 0 if processor.stats['failed_pdfs'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
