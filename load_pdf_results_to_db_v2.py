
import json
import logging
import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL not found")
        return

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    files = list(Path("outputs").rglob("pdf_processing_results.json"))
    logger.info(f"Found {len(files)} files")
    
    total_loaded = 0
    
    for f in files:
        rera_id = f.parent.name
        if rera_id == "outputs":
            continue
            
        # Get Project ID
        cur.execute("SELECT id FROM projects WHERE rera_registration_number = %s", (rera_id,))
        row = cur.fetchone()
        if not row:
            # Try ILIKE
            cur.execute("SELECT id FROM projects WHERE rera_registration_number ILIKE %s", (rera_id,))
            row = cur.fetchone()
            
        if not row:
            logger.warning(f"Project not found: {rera_id}")
            continue
            
        project_id = row[0]
        
        try:
            with open(f, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
                
            results = data.get("results", [])
            for res in results:
                fname = res.get("file")
                if not fname: continue
                
                doc_type = res.get("document_type") or res.get("type", "unknown")
                confidence = float(res.get("confidence") or 0.0)
                text_len = int(res.get("text_length") or 0)
                
                meta = res.get("metadata", {})
                app_num = meta.get("approval_number") or res.get("approval_number")
                app_date = meta.get("approval_date") or res.get("approval_date")
                
                duration = int(res.get("processing_time_ms") or (res.get("time_sec", 0) * 1000))
                
                # Upsert into document_extractions
                cur.execute("""
                    INSERT INTO document_extractions 
                    (project_id, filename, file_path, document_type, document_type_confidence, 
                     text_length, processing_time_ms, approval_number, approval_date, processor_name, success)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    project_id, fname, str(f.parent / fname), doc_type, confidence,
                    text_len, duration, app_num, app_date, "llm_gpu", True
                ))
                
                # Update project date if applicable
                if doc_type == "registration_certificate" and app_date and len(str(app_date)) == 10:
                    cur.execute("UPDATE projects SET approved_date = %s WHERE id = %s AND approved_date IS NULL", (app_date, project_id))
                
                total_loaded += 1
                
            conn.commit()
            logger.info(f"Loaded {rera_id}")
        except Exception as e:
            logger.error(f"Error loading {f}: {e}")
            conn.rollback()

    conn.close()
    logger.info(f"Total documents loaded: {total_loaded}")

if __name__ == "__main__":
    load_data()
