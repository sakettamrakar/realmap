"""Parallel PDF Downloader - Downloads PDFs for multiple runs concurrently.

This script:
1. Finds all runs that need PDF downloads
2. Downloads PDFs for multiple runs in parallel using ThreadPoolExecutor
3. Provides real-time progress tracking
4. Handles failures gracefully with retries

Usage:
    python parallel_pdf_downloader.py --workers 4
    python parallel_pdf_downloader.py --workers 8 --pages 1-25
    python parallel_pdf_downloader.py --retry-failed
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(threadName)-10s] - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)


class ParallelPDFDownloader:
    """Manages parallel PDF downloads across multiple runs."""
    
    def __init__(self, workers: int = 4):
        self.workers = min(workers, 4)  # Max 4 workers to avoid rate limiting
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'total_pdfs': 0,
            'start_time': time.time()
        }
        LOGGER.info(f"Initialized with {self.workers} parallel workers (max 4 for rate limiting)")
    
    def find_runs_needing_pdfs(
        self,
        pages: Optional[str] = None,
        retry_failed: bool = False
    ) -> List[Path]:
        """Find all runs that need PDF downloads."""
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
            
            # Find specific page directories
            for page_num in page_nums:
                page_dir = outputs_dir / f"parallel-page{page_num}"
                if page_dir.exists():
                    runs_dir = page_dir / "runs"
                    if runs_dir.exists():
                        runs.extend(runs_dir.glob("run_*"))
        else:
            # Find all parallel page runs
            for page_dir in outputs_dir.glob("parallel-page*"):
                runs_dir = page_dir / "runs"
                if runs_dir.exists():
                    runs.extend(runs_dir.glob("run_*"))
        
        # Filter runs based on status
        filtered_runs = []
        for run_dir in runs:
            if not run_dir.is_dir():
                continue
            
            scraped_json = run_dir / "scraped_json"
            if not scraped_json.exists() or not any(scraped_json.glob("*.json")):
                continue
            
            previews_dir = run_dir / "previews"
            
            # Check if PDFs need downloading
            if retry_failed:
                # Include runs with failed or incomplete downloads
                filtered_runs.append(run_dir)
            elif not previews_dir.exists():
                # No previews directory - needs download
                filtered_runs.append(run_dir)
            else:
                # Check if any projects need PDFs
                needs_download = False
                for project_dir in previews_dir.glob("*"):
                    if not project_dir.is_dir():
                        continue
                    
                    metadata_file = project_dir / "metadata.json"
                    if not metadata_file.exists():
                        needs_download = True
                        break
                    
                    # Check if download was incomplete
                    try:
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                            if metadata.get("failed", 0) > 0:
                                needs_download = True
                                break
                    except:
                        needs_download = True
                        break
                
                if needs_download:
                    filtered_runs.append(run_dir)
        
        return sorted(filtered_runs)
    
    def download_run(self, run_dir: Path) -> Tuple[bool, str, Dict]:
        """Download PDFs for a single run."""
        run_name = run_dir.name
        
        try:
            LOGGER.info(f"Starting: {run_name}")
            
            result = subprocess.run(
                [sys.executable, "download_pdfs.py", "--run-dir", str(run_dir)],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                # Parse output for stats
                output = result.stdout
                stats = self._parse_stats(output)
                LOGGER.info(f"✅ SUCCESS: {run_name} - {stats.get('downloaded', 0)} PDFs")
                return True, run_name, stats
            else:
                error = result.stderr[:200] if result.stderr else "Unknown error"
                LOGGER.error(f"❌ FAILED: {run_name} - {error}")
                return False, run_name, {'error': error}
                
        except subprocess.TimeoutExpired:
            LOGGER.error(f"⏰ TIMEOUT: {run_name}")
            return False, run_name, {'error': 'Timeout'}
        except Exception as e:
            LOGGER.error(f"❌ ERROR: {run_name} - {e}")
            return False, run_name, {'error': str(e)}
    
    def _parse_stats(self, output: str) -> Dict:
        """Parse download statistics from output."""
        stats = {}
        try:
            for line in output.split('\n'):
                if 'Downloaded:' in line:
                    # Extract number from "Downloaded: 15/20"
                    parts = line.split(':')[1].strip().split('/')
                    stats['downloaded'] = int(parts[0])
                    stats['total'] = int(parts[1]) if len(parts) > 1 else 0
                elif 'Failed:' in line:
                    stats['failed'] = int(line.split(':')[1].strip())
                elif 'Total size:' in line and 'MB' in line:
                    # Extract MB value
                    mb_str = line.split('(')[1].split('MB')[0].strip()
                    stats['size_mb'] = float(mb_str)
        except:
            pass
        
        return stats
    
    def download_all(
        self,
        pages: Optional[str] = None,
        retry_failed: bool = False
    ) -> None:
        """Download PDFs for all runs in parallel."""
        LOGGER.info("="*70)
        LOGGER.info("PARALLEL PDF DOWNLOADER")
        LOGGER.info("="*70)
        
        # Find runs
        LOGGER.info(f"Scanning for runs (pages={pages or 'all'})...")
        runs = self.find_runs_needing_pdfs(pages, retry_failed)
        
        if not runs:
            LOGGER.info("✅ No runs need PDF downloads!")
            return
        
        self.stats['total_runs'] = len(runs)
        
        LOGGER.info(f"Found {len(runs)} runs needing PDF downloads")
        LOGGER.info(f"Using {self.workers} parallel workers")
        LOGGER.info("="*70)
        
        # Process runs in parallel
        results = []
        failed_runs = []
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Submit all tasks
            future_to_run = {
                executor.submit(self.download_run, run_dir): run_dir
                for run_dir in runs
            }
            
            # Process completed tasks
            for future in as_completed(future_to_run):
                run_dir = future_to_run[future]
                try:
                    success, run_name, stats = future.result()
                    results.append((success, run_name, stats))
                    
                    if success:
                        self.stats['successful_runs'] += 1
                        self.stats['total_pdfs'] += stats.get('downloaded', 0)
                    else:
                        self.stats['failed_runs'] += 1
                        failed_runs.append((run_name, stats.get('error', 'Unknown')))
                    
                    # Progress update
                    completed = self.stats['successful_runs'] + self.stats['failed_runs']
                    LOGGER.info(
                        f"Progress: {completed}/{len(runs)} runs "
                        f"({self.stats['successful_runs']} success, "
                        f"{self.stats['failed_runs']} failed)"
                    )
                    
                except Exception as e:
                    LOGGER.error(f"Task failed for {run_dir.name}: {e}")
                    self.stats['failed_runs'] += 1
                    failed_runs.append((run_dir.name, str(e)))
        
        # Final summary
        elapsed = time.time() - self.stats['start_time']
        
        LOGGER.info("\n" + "="*70)
        LOGGER.info("DOWNLOAD COMPLETE")
        LOGGER.info("="*70)
        LOGGER.info(f"Total runs: {self.stats['total_runs']}")
        LOGGER.info(f"Successful: {self.stats['successful_runs']}")
        LOGGER.info(f"Failed: {self.stats['failed_runs']}")
        LOGGER.info(f"Total PDFs downloaded: {self.stats['total_pdfs']}")
        LOGGER.info(f"Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        LOGGER.info(f"Average: {elapsed/len(runs):.1f}s per run")
        
        if failed_runs:
            LOGGER.info("\nFailed runs:")
            for run_name, error in failed_runs[:10]:
                LOGGER.info(f"  ❌ {run_name}: {error[:50]}")
            if len(failed_runs) > 10:
                LOGGER.info(f"  ... and {len(failed_runs) - 10} more")
        
        LOGGER.info("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Download PDFs for multiple runs in parallel"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    parser.add_argument(
        "--pages",
        type=str,
        help="Page range or list (e.g., '1-25' or '1,2,3')"
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry runs with failed downloads"
    )
    
    args = parser.parse_args()
    
    downloader = ParallelPDFDownloader(workers=args.workers)
    downloader.download_all(pages=args.pages, retry_failed=args.retry_failed)
    
    return 0 if downloader.stats['failed_runs'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
