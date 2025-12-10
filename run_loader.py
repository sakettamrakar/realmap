
import os
import glob

# Find latest run
outputs_dir = "outputs/test-1project/runs"
runs = glob.glob(os.path.join(outputs_dir, "run_*"))
latest_run = max(runs, key=os.path.getctime)
print(f"Latest run: {latest_run}")

# Set DB URL
os.environ["DATABASE_URL"] = "postgresql://postgres:betsson%40123@localhost:5432/realmapdb"

# Call loader (assuming load_run takes the run directory)
# Check signature first??
try:
    # Actually, let's use the tool mentioned in README: tools/load_runs_to_db.py
    # But I can't run python tools/... easily if I don't know args.
    # Let's try running the tool directly via subprocess if this file is just a wrapper,
    # or just use the tool command directly in next step.
    pass
except Exception as e:
    print(e)
