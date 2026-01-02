
"""
Parallel LLM PDF Processor PRO - Enhanced version with incremental saves and DB loading.
This script ensures that results are saved immediately after each PDF is processed, 
preventing data loss during power failures or crashes.
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
import psycopg2
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables for LLM GPU processing
os.environ.setdefault("MODEL_PATH", "C:/models/ai/general/v1/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf")
os.environ.setdefault("GPU_LAYERS", "33")
os.environ.setdefault("AI_ENABLED", "true")
os.environ.setdefault("CONTEXT_SIZE", "4096")
os.environ.setdefault("LLM_TIMEOUT_SEC", "300")
os.environ.setdefault("LLM_ENABLE_SUMMARY", "false")

from ai.features.pdf_processing import (
    PDFOrchestrator,
    ProcessingMode,
    BatchResult,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(threadName)-10s] - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)

class IncrementalProcessor:
    def __init__(self, workers=1, mode=ProcessingMode.TEXT_ONLY, batch_size=10, load_db=False):
        self.workers = workers
        self.mode = mode
        self.batch_size = batch_size
        self.load_db = load_db
        self.db_url = os.getenv("DATABASE_URL")
        self.stats = {
            'processed': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': time.time()
        }

    def get_db_connection(self):
        if not self.db_url: return None
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            LOGGER.error(f"DB Connection failed: {e}")
            return None

    def load_to_db(self, project_id_str, result, results_file_path):
        conn = self.get_db_connection()
        if not conn: return False
        
        try:
            cur = conn.cursor()
            # Find project internal ID
            cur.execute("SELECT id FROM projects WHERE rera_registration_number = %s", (project_id_str,))
            row = cur.fetchone()
            if not row:
                cur.execute("SELECT id FROM projects WHERE rera_registration_number ILIKE %s", (project_id_str,))
                row = cur.fetchone()
            
            if not row:
                LOGGER.warning(f"Project {project_id_str} not found in DB")
                return False
                
            project_id = row[0]
            
            # Extraction details
            fname = result.filename
            doc_type = result.document_type.value if result.document_type else "unknown"
            confidence = float(result.document_type_confidence or 0.0)
            text_len = int(result.text_length or 0)
            meta = result.metadata
            app_num = meta.approval_number if meta else None
            app_date = meta.approval_date if meta else None
            duration = int(result.processing_time_ms or 0)
            
            cur.execute("""
                INSERT INTO document_extractions 
                (project_id, filename, file_path, document_type, document_type_confidence, 
                 text_length, processing_time_ms, approval_number, approval_date, processor_name, success)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (project_id, filename) DO UPDATE SET
                    document_type = EXCLUDED.document_type,
                    document_type_confidence = EXCLUDED.document_type_confidence,
                    approval_date = COALESCE(EXCLUDED.approval_date, document_extractions.approval_date),
                    success = EXCLUDED.success
            """, (
                project_id, fname, str(results_file_path.parent / fname), doc_type, confidence,
                text_len, duration, app_num, app_date, "llm_gpu_pro", result.success
            ))
            
            conn.commit()
            return True
        except Exception as e:
            LOGGER.error(f"DB Load Error for {project_id_str}/{result.filename}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def process_project(self, run_dir, rera_id, pdf_files):
        project_dir = pdf_files[0].parent
        results_file = project_dir / "pdf_processing_results.json"
        
        # Load existing results if any
        existing_results = {}
        if results_file.exists():
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for res in data.get('results', []):
                        existing_results[res['file']] = res
            except:
                pass

        orchestrator = PDFOrchestrator(
            text_max_pages=20,
            llm_max_pages=10,
            skip_processed=False
        )

        successful_in_project = 0
        processed_in_project = 0
        
        # Only process up to batch_size new files
        to_process = []
        for pdf in pdf_files:
            if pdf.name in existing_results and existing_results[pdf.name].get('success'):
                continue
            to_process.append(pdf)
            if len(to_process) >= self.batch_size:
                break
        
        if not to_process:
            return 0, 0, len(pdf_files) # processed, success, skipped

        LOGGER.info(f"Project {rera_id}: Processing {len(to_process)} new PDFs (Total: {len(pdf_files)})")

        for pdf_path in to_process:
            try:
                result = orchestrator.process_file(pdf_path, self.mode)
                processed_in_project += 1
                
                # Update existing results
                res_dict = {
                    "file": result.filename,
                    "success": result.success,
                    "document_type": result.document_type.value if result.document_type else None,
                    "confidence": result.document_type_confidence,
                    "page_count": result.page_count,
                    "text_length": result.text_length,
                    "processing_time_ms": int(time.time()*1000), # Placeholder for real time
                    "metadata": {
                        "approval_number": result.metadata.approval_number if result.metadata else None,
                        "approval_date": result.metadata.approval_date if result.metadata else None,
                        "issuing_authority": result.metadata.issuing_authority if result.metadata else None,
                        "summary": result.metadata.summary if result.metadata else None,
                    } if result.metadata else None,
                    "error": result.error,
                }
                existing_results[pdf_path.name] = res_dict
                
                # INCREMENTAL SAVE TO JSON
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump({"results": list(existing_results.values())}, f, indent=2)
                
                if result.success:
                    successful_in_project += 1
                    # OPTIONAL DB LOAD
                    if self.load_db:
                        self.load_to_db(rera_id, result, results_file)
                
                LOGGER.info(f"  [{rera_id}] Processed {pdf_path.name}: {'✅' if result.success else '❌'}")
                
            except Exception as e:
                LOGGER.error(f"  [{rera_id}] Failed {pdf_path.name}: {e}")

        return processed_in_project, successful_in_project, 0

    def find_all_pdfs(self, pages=None):
        outputs_dir = Path("outputs")
        all_work = []
        
        # Find all 'previews' directories anywhere inside outputs
        previews_dirs = list(outputs_dir.glob("**/previews"))
        
        if pages:
            # If pages filter is provided, we still want to respect it
            # But the current structure might be nested differently
            # For now, let's keep it simple and scan everything if pages is None
            # or filter if we can identify the page
            pass

        for p_dir in previews_dirs:
            # Check if this previews dir is inside a 'run_*' dir
            run_dir = p_dir.parent
            if not run_dir.name.startswith("run_"):
                continue
                
            for project in p_dir.glob("*"):
                if not project.is_dir(): continue
                pdfs = list(project.glob("*.pdf"))
                if pdfs:
                    all_work.append((run_dir, project.name, pdfs))
        
        return all_work

    def run(self, pages=None):
        work = self.find_all_pdfs(pages)
        LOGGER.info(f"Found {len(work)} projects to check.")
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = [executor.submit(self.process_project, r, i, p) for r, i, p in work]
            
            for future in as_completed(futures):
                proc, succ, skip = future.result()
                self.stats['processed'] += proc
                self.stats['success'] += succ
                self.stats['skipped'] += skip
                
                elapsed = time.time() - self.stats['start_time']
                LOGGER.info(f"PROGRESS: Processed {self.stats['processed']} PDFs, {self.stats['success']} Success, {self.stats['skipped']} Skipped. Time: {elapsed/60:.1f}m")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--pages", type=str)
    parser.add_argument("--mode", type=str, default="hybrid")
    parser.add_argument("--load-db", action="store_true", help="Load to DB immediately")
    
    args = parser.parse_args()
    
    proc = IncrementalProcessor(
        workers=args.workers,
        mode=args.mode,
        batch_size=args.batch_size,
        load_db=args.load_db
    )
    proc.run(pages=args.pages)

if __name__ == "__main__":
    main()
