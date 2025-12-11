"""Process saved HTML files into V1 JSON format for a run directory."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from cg_rera_extractor.parsing.mapper import map_raw_to_v1
from cg_rera_extractor.parsing.raw_extractor import extract_raw_from_html

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def process_run(run_dir: Path, state_code: str = "CG") -> dict[str, int]:
    """Process HTML files in a run directory into V1 JSON."""
    
    raw_html_dir = run_dir / "raw_html"
    raw_extracted_dir = run_dir / "raw_extracted"
    scraped_json_dir = run_dir / "scraped_json"
    
    # Create output directories
    raw_extracted_dir.mkdir(exist_ok=True)
    scraped_json_dir.mkdir(exist_ok=True)
    
    html_files = sorted(raw_html_dir.glob("*.html"))
    
    if not html_files:
        logger.warning(f"No HTML files found in {raw_html_dir}")
        return {"processed": 0, "failed": 0}
    
    logger.info(f"Found {len(html_files)} HTML files to process")
    
    processed = 0
    failed = 0
    
    for html_file in html_files:
        try:
            logger.info(f"Processing {html_file.name}...")
            
            # Read HTML
            html = html_file.read_text(encoding="utf-8")
            
            # Extract registration number from filename
            # Format: project_{state_code}_{reg_no}.html
            project_key = html_file.stem.replace("project_", "", 1)
            reg_no = None
            if project_key.startswith(f"{state_code}_"):
                reg_no = project_key[len(state_code) + 1:]
            
            # Extract raw data
            raw = extract_raw_from_html(
                html, 
                source_file=str(html_file),
                registration_number=reg_no
            )
            
            # Save raw extracted JSON
            raw_path = raw_extracted_dir / f"{html_file.stem}.json"
            raw_path.write_text(
                json.dumps(raw.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            
            # Map to V1 schema
            v1_project = map_raw_to_v1(raw, state_code=state_code)
            
            # Save V1 JSON
            v1_path = scraped_json_dir / f"{html_file.stem}.v1.json"
            v1_path.write_text(
                json.dumps(
                    v1_project.model_dump(mode="json", exclude_none=True),
                    ensure_ascii=False,
                    indent=2
                ),
                encoding="utf-8"
            )
            
            logger.info(f"✓ Processed {html_file.name} -> {v1_path.name}")
            processed += 1
            
        except Exception as exc:
            logger.error(f"✗ Failed to process {html_file.name}: {exc}")
            failed += 1
    
    return {"processed": processed, "failed": failed}


def main():
    parser = argparse.ArgumentParser(
        description="Process HTML files into V1 JSON for a run directory"
    )
    parser.add_argument(
        "run_dir",
        help="Path to run directory (e.g., outputs/raipur-20/runs/run_20251210_090333_f88ae6)"
    )
    parser.add_argument(
        "--state-code",
        default="CG",
        help="State code for the projects (default: CG)"
    )
    
    args = parser.parse_args()
    run_path = Path(args.run_dir)
    
    if not run_path.exists():
        print(f"Error: Run directory does not exist: {run_path}")
        return 1
    
    if not (run_path / "raw_html").exists():
        print(f"Error: raw_html directory not found in {run_path}")
        return 1
    
    print(f"\n{'='*70}")
    print("HTML to V1 JSON Processor")
    print(f"{'='*70}")
    print(f"Run directory: {run_path}")
    print(f"State code:    {args.state_code}")
    print()
    
    stats = process_run(run_path, state_code=args.state_code)
    
    print(f"\n{'='*70}")
    print("Processing Summary")
    print(f"{'='*70}")
    print(f"Processed: {stats['processed']}")
    print(f"Failed:    {stats['failed']}")
    
    if stats['processed'] > 0:
        print(f"\n✓ Successfully processed {stats['processed']} HTML files")
        print(f"  → Raw extracted: {run_path / 'raw_extracted'}")
        print(f"  → V1 JSON:       {run_path / 'scraped_json'}")
    
    return 0 if stats['failed'] == 0 else 1


if __name__ == "__main__":
    exit(main())
