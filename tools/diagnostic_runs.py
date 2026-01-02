
from pathlib import Path
base_output = Path(r"c:\GIT\realmap\outputs")
candidates = []
for run_dir in base_output.rglob("run_*"):
    if run_dir.is_dir() and (run_dir / "scraped_json").exists():
        candidates.append(str(run_dir))
print(f"Found {len(candidates)} candidates")
for c in candidates[:5]:
    print(c)
