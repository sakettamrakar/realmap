"""Complete Parallel Processing Pipeline - Orchestrates PDF download and LLM processing.

This master script:
1. Can run PDF download and LLM processing simultaneously in separate processes
2. Or run them sequentially with optimal settings
3. Provides unified progress tracking and reporting

Architecture:
- PDF Download: Uses threading for I/O-bound network operations
- LLM Processing: Uses separate processes for CPU/GPU-bound operations
- Both can run concurrently since they access different resources

Usage:
    # Run both in parallel (recommended)
    python pipeline_orchestrator.py --mode parallel --pages 1-10
    
    # Run sequentially (download first, then process)
    python pipeline_orchestrator.py --mode sequential --pages 1-10
    
    # Only download PDFs
    python pipeline_orchestrator.py --download-only --pages 1-10
    
    # Only process PDFs
    python pipeline_orchestrator.py --process-only --pages 1-10 --llm-mode text_only
    
    # Custom worker counts
    python pipeline_orchestrator.py --download-workers 8 --process-workers 2
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from multiprocessing import Process, Queue
from pathlib import Path
from typing import Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the complete PDF download and processing pipeline."""
    
    def __init__(
        self,
        download_workers: int = 4,
        process_workers: int = 2,
        llm_mode: str = 'text_only'
    ):
        self.download_workers = download_workers
        self.process_workers = process_workers
        self.llm_mode = llm_mode
        self.stats = {
            'start_time': time.time(),
            'download_complete': False,
            'processing_complete': False,
            'download_stats': {},
            'processing_stats': {}
        }
    
    def run_download(
        self,
        pages: Optional[str] = None,
        retry_failed: bool = False,
        stats_queue: Optional[Queue] = None
    ) -> int:
        """Run PDF download subprocess."""
        LOGGER.info("="*70)
        LOGGER.info("STARTING PDF DOWNLOAD PROCESS")
        LOGGER.info("="*70)
        
        cmd = [
            sys.executable,
            "parallel_pdf_downloader.py",
            "--workers", str(self.download_workers)
        ]
        
        if pages:
            cmd.extend(["--pages", pages])
        
        if retry_failed:
            cmd.append("--retry-failed")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse stats from output
            stats = self._parse_download_stats(result.stdout)
            self.stats['download_stats'] = stats
            self.stats['download_complete'] = True
            
            if stats_queue:
                stats_queue.put(('download', stats))
            
            LOGGER.info("PDF download process completed")
            LOGGER.info(f"Return code: {result.returncode}")
            
            if result.returncode != 0:
                LOGGER.error(f"Download failed with errors:\n{result.stderr}")
            
            return result.returncode
            
        except Exception as e:
            LOGGER.error(f"Download process failed: {e}")
            return 1
    
    def run_processing(
        self,
        pages: Optional[str] = None,
        skip_processed: bool = False,
        stats_queue: Optional[Queue] = None
    ) -> int:
        """Run LLM processing subprocess."""
        LOGGER.info("="*70)
        LOGGER.info("STARTING LLM PROCESSING PROCESS")
        LOGGER.info("="*70)
        
        cmd = [
            sys.executable,
            "parallel_llm_processor.py",
            "--workers", str(self.process_workers),
            "--mode", self.llm_mode
        ]
        
        if pages:
            cmd.extend(["--pages", pages])
        
        if skip_processed:
            cmd.append("--skip-processed")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse stats from output
            stats = self._parse_processing_stats(result.stdout)
            self.stats['processing_stats'] = stats
            self.stats['processing_complete'] = True
            
            if stats_queue:
                stats_queue.put(('processing', stats))
            
            LOGGER.info("LLM processing completed")
            LOGGER.info(f"Return code: {result.returncode}")
            
            if result.returncode != 0:
                LOGGER.error(f"Processing failed with errors:\n{result.stderr}")
            
            return result.returncode
            
        except Exception as e:
            LOGGER.error(f"Processing failed: {e}")
            return 1
    
    def _parse_download_stats(self, output: str) -> Dict:
        """Parse download statistics from output."""
        stats = {}
        try:
            for line in output.split('\n'):
                if 'Total runs:' in line:
                    stats['total_runs'] = int(line.split(':')[1].strip())
                elif 'Successful:' in line:
                    stats['successful'] = int(line.split(':')[1].strip())
                elif 'Failed:' in line:
                    stats['failed'] = int(line.split(':')[1].strip())
                elif 'Total PDFs downloaded:' in line:
                    stats['total_pdfs'] = int(line.split(':')[1].strip())
                elif 'Total time:' in line and 'minutes' in line:
                    time_str = line.split('(')[1].split('minutes')[0].strip()
                    stats['time_minutes'] = float(time_str)
        except Exception as e:
            LOGGER.warning(f"Failed to parse download stats: {e}")
        
        return stats
    
    def _parse_processing_stats(self, output: str) -> Dict:
        """Parse processing statistics from output."""
        stats = {}
        try:
            for line in output.split('\n'):
                if 'Total PDFs:' in line:
                    stats['total_pdfs'] = int(line.split(':')[1].strip())
                elif 'Processed:' in line and 'Total' not in line:
                    stats['processed'] = int(line.split(':')[1].strip())
                elif 'Successful:' in line:
                    stats['successful'] = int(line.split(':')[1].strip())
                elif 'Failed:' in line:
                    stats['failed'] = int(line.split(':')[1].strip())
                elif 'Success rate:' in line:
                    rate_str = line.split(':')[1].strip().rstrip('%')
                    stats['success_rate'] = float(rate_str)
                elif 'Total time:' in line and 'minutes' in line:
                    time_str = line.split('(')[1].split('minutes')[0].strip()
                    stats['time_minutes'] = float(time_str)
        except Exception as e:
            LOGGER.warning(f"Failed to parse processing stats: {e}")
        
        return stats
    
    def run_parallel(
        self,
        pages: Optional[str] = None,
        retry_failed: bool = False,
        skip_processed: bool = False
    ) -> int:
        """Run download and processing in parallel."""
        LOGGER.info("="*70)
        LOGGER.info("PARALLEL PIPELINE MODE")
        LOGGER.info("="*70)
        LOGGER.info(f"Download workers: {self.download_workers}")
        LOGGER.info(f"Process workers: {self.process_workers}")
        LOGGER.info(f"LLM mode: {self.llm_mode}")
        LOGGER.info(f"Pages: {pages or 'all'}")
        LOGGER.info("="*70)
        
        stats_queue = Queue()
        
        # Start both processes
        download_proc = Process(
            target=self.run_download,
            args=(pages, retry_failed, stats_queue)
        )
        
        # Give download a head start (30 seconds)
        download_proc.start()
        time.sleep(30)
        
        process_proc = Process(
            target=self.run_processing,
            args=(pages, skip_processed, stats_queue)
        )
        process_proc.start()
        
        # Wait for both to complete
        download_proc.join()
        process_proc.join()
        
        # Collect stats
        while not stats_queue.empty():
            proc_type, stats = stats_queue.get()
            if proc_type == 'download':
                self.stats['download_stats'] = stats
            else:
                self.stats['processing_stats'] = stats
        
        # Print summary
        self._print_summary()
        
        return 0 if (download_proc.exitcode == 0 and process_proc.exitcode == 0) else 1
    
    def run_sequential(
        self,
        pages: Optional[str] = None,
        retry_failed: bool = False,
        skip_processed: bool = False
    ) -> int:
        """Run download then processing sequentially."""
        LOGGER.info("="*70)
        LOGGER.info("SEQUENTIAL PIPELINE MODE")
        LOGGER.info("="*70)
        LOGGER.info("Step 1: Download PDFs")
        LOGGER.info("Step 2: Process PDFs with LLM")
        LOGGER.info("="*70)
        
        # Step 1: Download
        download_result = self.run_download(pages, retry_failed)
        
        if download_result != 0:
            LOGGER.error("Download failed, skipping processing")
            return download_result
        
        LOGGER.info("\n" + "="*70)
        LOGGER.info("Download complete, starting processing...")
        LOGGER.info("="*70 + "\n")
        
        # Step 2: Process
        process_result = self.run_processing(pages, skip_processed)
        
        # Print summary
        self._print_summary()
        
        return process_result
    
    def _print_summary(self):
        """Print final pipeline summary."""
        elapsed = time.time() - self.stats['start_time']
        
        LOGGER.info("\n" + "="*70)
        LOGGER.info("PIPELINE COMPLETE")
        LOGGER.info("="*70)
        
        # Download stats
        if self.stats['download_stats']:
            ds = self.stats['download_stats']
            LOGGER.info("\nDownload Summary:")
            LOGGER.info(f"  Runs processed: {ds.get('successful', 0)}/{ds.get('total_runs', 0)}")
            LOGGER.info(f"  PDFs downloaded: {ds.get('total_pdfs', 0)}")
            LOGGER.info(f"  Time: {ds.get('time_minutes', 0):.1f} minutes")
        
        # Processing stats
        if self.stats['processing_stats']:
            ps = self.stats['processing_stats']
            LOGGER.info("\nProcessing Summary:")
            LOGGER.info(f"  PDFs processed: {ps.get('processed', 0)}/{ps.get('total_pdfs', 0)}")
            LOGGER.info(f"  Successful: {ps.get('successful', 0)}")
            LOGGER.info(f"  Failed: {ps.get('failed', 0)}")
            if 'success_rate' in ps:
                LOGGER.info(f"  Success rate: {ps['success_rate']:.1f}%")
            LOGGER.info(f"  Time: {ps.get('time_minutes', 0):.1f} minutes")
        
        LOGGER.info(f"\nTotal pipeline time: {elapsed/60:.1f} minutes")
        LOGGER.info("="*70)
        
        # Save summary to file
        summary_file = Path("outputs") / f"pipeline_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        summary_file.parent.mkdir(exist_ok=True)
        
        with open(summary_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
        
        LOGGER.info(f"\nSummary saved to: {summary_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Complete PDF download and processing pipeline orchestrator"
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--mode",
        choices=['parallel', 'sequential'],
        default='parallel',
        help="Pipeline mode (default: parallel)"
    )
    mode_group.add_argument(
        "--download-only",
        action="store_true",
        help="Only run PDF download"
    )
    mode_group.add_argument(
        "--process-only",
        action="store_true",
        help="Only run LLM processing"
    )
    
    # Common options
    parser.add_argument(
        "--pages",
        type=str,
        help="Page range or list (e.g., '1-25' or '1,2,3')"
    )
    
    # Download options
    parser.add_argument(
        "--download-workers",
        type=int,
        default=4,
        help="Number of parallel download workers (default: 4)"
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry failed downloads"
    )
    
    # Processing options
    parser.add_argument(
        "--process-workers",
        type=int,
        default=2,
        help="Number of parallel processing workers (default: 2)"
    )
    parser.add_argument(
        "--llm-mode",
        choices=['text_only', 'llm_only', 'hybrid', 'auto'],
        default='text_only',
        help="LLM processing mode (default: text_only)"
    )
    parser.add_argument(
        "--skip-processed",
        action="store_true",
        help="Skip already processed PDFs"
    )
    
    args = parser.parse_args()
    
    orchestrator = PipelineOrchestrator(
        download_workers=args.download_workers,
        process_workers=args.process_workers,
        llm_mode=args.llm_mode
    )
    
    # Execute based on mode
    if args.download_only:
        return orchestrator.run_download(args.pages, args.retry_failed)
    elif args.process_only:
        return orchestrator.run_processing(args.pages, args.skip_processed)
    elif args.mode == 'parallel':
        return orchestrator.run_parallel(
            args.pages,
            args.retry_failed,
            args.skip_processed
        )
    else:  # sequential
        return orchestrator.run_sequential(
            args.pages,
            args.retry_failed,
            args.skip_processed
        )


if __name__ == "__main__":
    sys.exit(main())
