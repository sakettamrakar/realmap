#!/usr/bin/env python
"""Test amenity extraction on real sample HTML."""

from pathlib import Path
from cg_rera_extractor.parsing.amenity_extractor import extract_amenity_locations, compute_centroid


def main():
    # Test on known HTML file with amenities
    html_path = Path("outputs/realcrawl/runs/run_20251121_113347_558ae6/raw_html/project_CG_PCGRERA240218000002.html")
    
    if not html_path.exists():
        print(f"HTML file not found: {html_path}")
        return
    
    html = html_path.read_text(encoding="utf-8")
    
    # Extract amenity locations
    locs = extract_amenity_locations(html)
    
    print(f"Found {len(locs)} amenity locations")
    print()
    
    for i, loc in enumerate(locs[:5], 1):
        print(f"{i}. {loc.source_type}: {loc.particulars}")
        print(f"   Location: ({loc.latitude:.6f}, {loc.longitude:.6f})")
        if loc.image_url:
            print(f"   Image: {loc.image_url}")
        if loc.from_date:
            print(f"   Date: {loc.from_date} - {loc.to_date}")
        if loc.progress_percent:
            print(f"   Progress: {loc.progress_percent}%")
        print()
    
    if len(locs) > 5:
        print(f"... and {len(locs) - 5} more locations")
        print()
    
    # Compute centroid
    centroid = compute_centroid(locs)
    if centroid:
        print(f"Centroid of all amenity locations: ({centroid[0]:.6f}, {centroid[1]:.6f})")


if __name__ == "__main__":
    main()
