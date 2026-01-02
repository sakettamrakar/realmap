
import logging
import sys
from cg_rera_extractor.db.loader import load_run_into_db
from cg_rera_extractor.db.init_db import init_db

logging.basicConfig(level=logging.DEBUG)

run_path = r"c:\GIT\realmap\outputs\parallel-page7\runs\run_20251214_073108_136e82"
try:
    print(f"Initializing DB...")
    init_db()
    print(f"Loading run: {run_path}")
    stats = load_run_into_db(run_path)
    print(f"Stats: {stats}")
except Exception as e:
    import traceback
    traceback.print_exc()
