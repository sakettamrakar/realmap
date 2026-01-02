
import os
import time
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("monitor_loader.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_loader():
    logger.info("Starting database load cycle...")
    try:
        # Run the existing v2 loader script
        result = subprocess.run(
            ["python", "load_pdf_results_to_db_v2.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("Load cycle complete.")
            # Optionally log a summary of what was loaded
            for line in result.stdout.splitlines():
                if "Total documents loaded" in line or "Loaded" in line:
                    logger.info(f"  {line}")
        else:
            logger.error(f"Loader failed with error: {result.stderr}")
    except Exception as e:
        logger.error(f"Error during load cycle: {e}")

def main():
    logger.info("="*60)
    logger.info("PDF RESULTS MONITOR & DB LOADER")
    logger.info("Will run every 5 minutes. Press Ctrl+C to stop.")
    logger.info("="*60)
    
    interval = 300 # 5 minutes
    
    try:
        while True:
            start_time = time.time()
            run_loader()
            
            elapsed = time.time() - start_time
            wait_time = max(0, interval - elapsed)
            
            if wait_time > 0:
                logger.info(f"Waiting {wait_time:.1f}s for next cycle...")
                time.sleep(wait_time)
            else:
                logger.warning("Load cycle took longer than 5 minutes, starting next immediately.")
                
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user.")

if __name__ == "__main__":
    main()
