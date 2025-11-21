ARCHIVED - superseded by README.md and docs/DEV_GUIDE.md.

# Cleanup Quick Reference

## One-Liner Usage

```bash
# Clean everything (safe - doesn't touch important files)
python tools/cleanup_temp_files.py

# Preview what would be deleted
python tools/cleanup_temp_files.py --dry-run

# Also clean run output directories
python tools/cleanup_temp_files.py --include-runs

# Also clean IDE configs
python tools/cleanup_temp_files.py --include-ide

# Do everything and preview first
python tools/cleanup_temp_files.py --include-runs --include-ide --dry-run
```

## What Gets Cleaned

### Always Cleaned
- `__pycache__/` directories (everywhere)
- `.pytest_cache/`
- `.mypy_cache/`
- `.ruff_cache/`
- `*.egg-info/` directories
- `*.log` files
- `.coverage` files
- `htmlcov/` directories

### Only with `--include-runs`
- `outputs/realcrawl/runs/`
- `outputs/debug_runs/`
- `outputs/phase2_runs/`

### Only with `--include-ide`
- `.idea/`
- `.vscode/`
- `.DS_Store`

## Gitignore Coverage

Everything you delete with the cleanup script is also in `.gitignore`, so it won't be accidentally committed.

## Safe to Run?

**Yes!** The script only deletes:
1. Generated caches (regenerated automatically)
2. Runtime logs (not needed after execution)
3. Build artifacts (regenerated when needed)

It explicitly does NOT touch:
- Source code
- Test files
- Configuration files
- Documentation
- Data samples

