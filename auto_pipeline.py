
import subprocess
import time
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auto_pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_command(cmd_list):
    logger.info(f"Running: {' '.join(cmd_list)}")
    try:
        # We use a timeout to prevent hanging forever
        # and capture output to log it
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True
        )
        if result.stdout:
            # Log only the summary lines to keep log clean
            for line in result.stdout.splitlines():
                if "Progress" in line or "Total" in line or "SUCCESS" in line or "FAILED" in line:
                    logger.info(f"  [STDOUT] {line}")
        if result.stderr:
            logger.error(f"  [STDERR] {result.stderr}")
        return result.returncode
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return 1

def main():
    logger.info("="*60)
    logger.info("MASTER AUTO-PIPELINE STARTED")
    logger.info("This will Download -> Process -> Load every cycle")
    logger.info("="*60)

    # Note: Using small batch sizes per project to ensure quick cycles
    # but scanning all pages to be complete.
    
    while True:
        cycle_start = time.time()
        
        # 1. Download missing PDFs
        logger.info("Cycle Step 1: Downloading PDFs...")
        run_command([sys.executable, "parallel_pdf_downloader.py", "--workers", "4"])
        
        # 2. Process with LLM and Load to DB
        # Using the Pro version with --load-db and 1 worker for GPU
        logger.info("Cycle Step 2: Processing PDFs & Loading to DB...")
        run_command([sys.executable, "parallel_llm_processor_pro.py", "--workers", "1", "--mode", "hybrid", "--load-db", "--batch-size", "50"])
        
        elapsed = time.time() - cycle_start
        wait_time = max(60, 300 - elapsed) # At least 1 minute wait, target 5 minute cycle
        
        logger.info(f"Cycle complete in {elapsed/60:.1f} minutes. Waiting {wait_time/60:.1f} minutes for next cycle...")
        time.sleep(wait_time)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user.")
