"""Parse existing HTML files from data/ folder using updated parsing logic."""
import json
import logging
from pathlib import Path

from cg_rera_extractor.parsing.mapper import map_raw_to_v1
from cg_rera_extractor.parsing.raw_extractor import extract_raw_from_html

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def parse_html_file(html_path: Path, state_code: str = "CG"):
    """Parse a single HTML file and return V1 project data."""
    try:
        html_content = html_path.read_text(encoding="utf-8")
        
        logger.info(f"Processing {html_path.name}...")
        
        # Extract raw data from HTML using the parsing logic
        raw = extract_raw_from_html(
            html_content,
            source_file=str(html_path),
            registration_number=None
        )
        
        # Map to V1 schema
        v1_project = map_raw_to_v1(raw, state_code=state_code)
        
        logger.info(f"✓ Successfully parsed {html_path.name}")
        return v1_project
    except Exception as exc:
        logger.error(f"✗ Failed to parse {html_path.name}: {exc}")
        return None


def main():
    data_dir = Path("data")
    output_dir = Path("outputs/parsed_html")
    state_code = "CG"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find HTML files in data/
    html_files = list(data_dir.glob("*.htm")) + list(data_dir.glob("*.html"))
    
    if not html_files:
        logger.warning(f"No HTML files found in {data_dir}")
        return
    
    logger.info(f"Found {len(html_files)} HTML files to parse")
    print(f"\n{'='*70}")
    print("HTML Parser - Using Updated Parsing Logic")
    print(f"{'='*70}")
    print(f"Data directory:  {data_dir.resolve()}")
    print(f"Output directory: {output_dir.resolve()}")
    print(f"State code:      {state_code}")
    print()
    
    processed = 0
    failed = 0
    projects = []
    
    for html_file in html_files:
        v1_project = parse_html_file(html_file, state_code)
        if v1_project:
            projects.append(v1_project)
            processed += 1
        else:
            failed += 1
    
    # Save all projects to a single JSON file for loading
    if projects:
        output_json = output_dir / "parsed_projects.json"
        projects_data = [p.model_dump(mode="json", exclude_none=True) for p in projects]
        output_json.write_text(
            json.dumps(projects_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        logger.info(f"Saved {len(projects)} projects to {output_json}")
    
    # Print summary
    print(f"\n{'='*70}")
    print("Parsing Summary")
    print(f"{'='*70}")
    print(f"Processed: {processed}")
    print(f"Failed:    {failed}")
    print(f"Total:     {processed + failed}")
    
    if processed > 0:
        print(f"\n✓ Successfully parsed {processed} HTML files")
        print(f"  Output: {output_dir / 'parsed_projects.json'}")
    
    return processed, failed


if __name__ == "__main__":
    main()
