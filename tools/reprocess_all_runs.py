
from pathlib import Path
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator")

def main():
    base_output = Path(r"c:\GIT\realmap\outputs")
    # Find all run directories with raw_html
    run_dirs = []
    for p in base_output.rglob("run_*"):
        if p.is_dir() and (p / "raw_html").exists():
            run_dirs.append(p)
            
    print(f"Found {len(run_dirs)} runs with raw_html to re-process and load.")
    
    for i, run_dir in enumerate(run_dirs):
        print(f"\n[{i+1}/{len(run_dirs)}] STEP A: Reprocessing HTML for {run_dir}...")
        try:
            # Call process_html_to_json.py
            cmd = [sys.executable, str(Path(r"c:\GIT\realmap\tools\process_html_to_json.py")), str(run_dir)]
            subprocess.run(cmd, check=True, capture_output=True)
            
            print(f"[{i+1}/{len(run_dirs)}] STEP B: Loading into DB...")
            # We'll use a modified one-run loader logic here to avoid overhead
            from cg_rera_extractor.db.loader import load_run_into_db
            try:
                # We use load_run_into_db which we know works now that we fixed LoadStats
                # We wrap it to ignore the migration failures we saw earlier in setup_and_load
                stats = load_run_into_db(str(run_dir))
                print(f"  -> Added {stats.get('units', 0)} units.")
            except Exception as e:
                print(f"  -> DB Load failed for {run_dir}: {e}")
                
        except Exception as e:
            print(f"Failed to process {run_dir}: {e}")
            
    print("\nIncremental processing and loading complete.")

if __name__ == "__main__":
    main()
