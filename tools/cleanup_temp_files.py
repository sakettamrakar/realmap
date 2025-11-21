#!/usr/bin/env python3
"""
Cleanup helper script to remove temporary, cache, and build artifacts.

Usage:
    python tools/cleanup_temp_files.py                 # Clean caches only
    python tools/cleanup_temp_files.py --include-runs  # Also clean outputs/runs
    python tools/cleanup_temp_files.py --help          # Show help
"""

import argparse
import shutil
import sys
from pathlib import Path

# Standard cache and temporary patterns to clean
CACHE_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
    "htmlcov",
]

LOG_PATTERNS = [
    "*.log",
]

# Build/generated patterns
BUILD_PATTERNS = [
    ".eggs",
    "*.egg-info",
    ".build",
]

# Run output patterns (optional cleanup with --include-runs)
RUN_PATTERNS = [
    "outputs/realcrawl/runs",
    "outputs/debug_runs",
    "outputs/phase2_runs",
]

# Editor/IDE patterns
IDE_PATTERNS = [
    ".idea",
    ".vscode",
    ".DS_Store",
]


def clean_directory(base_path: Path, pattern: str, recursive: bool = True) -> int:
    """Remove files/dirs matching pattern.
    
    Returns count of deleted items.
    """
    deleted_count = 0
    
    if "*" in pattern:
        # Glob pattern
        if recursive:
            items = list(base_path.rglob(pattern))
        else:
            items = list(base_path.glob(pattern))
    else:
        # Exact directory name
        if recursive:
            items = list(base_path.rglob(pattern))
        else:
            item = base_path / pattern
            items = [item] if item.exists() else []
    
    for item in items:
        try:
            if item.is_dir():
                shutil.rmtree(item)
                print(f"  Deleted: {item.relative_to(base_path)}/")
                deleted_count += 1
            elif item.is_file():
                item.unlink()
                print(f"  Deleted: {item.relative_to(base_path)}")
                deleted_count += 1
        except Exception as e:
            print(f"  Error deleting {item}: {e}", file=sys.stderr)
    
    return deleted_count


def main():
    parser = argparse.ArgumentParser(
        description="Clean up temporary files, caches, and build artifacts."
    )
    parser.add_argument(
        "--include-runs",
        action="store_true",
        help="Also delete outputs/runs directories (careful!)",
    )
    parser.add_argument(
        "--include-ide",
        action="store_true",
        help="Also delete IDE/editor config directories (.idea, .vscode, etc.)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    args = parser.parse_args()
    
    repo_root = Path(__file__).parent.parent
    
    print(f"Cleaning up temporary files in: {repo_root}")
    print()
    
    total_deleted = 0
    
    # Clean caches
    print("Removing Python caches...")
    for pattern in CACHE_PATTERNS:
        if args.dry_run:
            items = list(repo_root.rglob(pattern))
            for item in items:
                print(f"  Would delete: {item.relative_to(repo_root)}")
            total_deleted += len(items)
        else:
            deleted = clean_directory(repo_root, pattern, recursive=True)
            total_deleted += deleted
    
    # Clean build artifacts
    print("\nRemoving build artifacts...")
    for pattern in BUILD_PATTERNS:
        if args.dry_run:
            items = list(repo_root.rglob(pattern))
            for item in items:
                print(f"  Would delete: {item.relative_to(repo_root)}")
            total_deleted += len(items)
        else:
            deleted = clean_directory(repo_root, pattern, recursive=True)
            total_deleted += deleted
    
    # Clean logs
    print("\nRemoving log files...")
    for pattern in LOG_PATTERNS:
        if args.dry_run:
            items = list(repo_root.rglob(pattern))
            for item in items:
                print(f"  Would delete: {item.relative_to(repo_root)}")
            total_deleted += len(items)
        else:
            deleted = clean_directory(repo_root, pattern, recursive=True)
            total_deleted += deleted
    
    # IDE configs (optional)
    if args.include_ide:
        print("\nRemoving IDE/editor configs...")
        for pattern in IDE_PATTERNS:
            if args.dry_run:
                item = repo_root / pattern
                if item.exists():
                    print(f"  Would delete: {item.relative_to(repo_root)}")
                    total_deleted += 1
            else:
                deleted = clean_directory(repo_root, pattern, recursive=False)
                total_deleted += deleted
    
    # Run outputs (optional)
    if args.include_runs:
        print("\nRemoving run output directories (--include-runs)...")
        for pattern in RUN_PATTERNS:
            if args.dry_run:
                item = repo_root / pattern
                if item.exists():
                    print(f"  Would delete: {item.relative_to(repo_root)}")
                    total_deleted += 1
            else:
                item = repo_root / pattern
                if item.exists():
                    try:
                        shutil.rmtree(item)
                        print(f"  Deleted: {item.relative_to(repo_root)}/")
                        total_deleted += 1
                    except Exception as e:
                        print(f"  Error deleting {item}: {e}", file=sys.stderr)
    
    print()
    if args.dry_run:
        print(f"Dry run: Would delete {total_deleted} items")
    else:
        print(f"✓ Cleanup complete. Deleted {total_deleted} items.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
