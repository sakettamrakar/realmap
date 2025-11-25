"""Utilities for extracting amenities lat/lon data from CG RERA detail pages."""

from __future__ import annotations

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup, Tag

from .schema import V1ReraLocation

LOGGER = logging.getLogger(__name__)

# Table IDs used in CG RERA detail pages for amenities
AMENITIES_TABLE_ID = "ContentPlaceHolder1_Single_gv_ProjectList"
AMENITIES_TABLE_ID_ALT = "ContentPlaceHolder1_gv_Amenity"  # Possible alternative ID

# Regex patterns to extract coordinates from Google Maps embed URL
# Format: !2d<longitude>!3d<latitude> (note: 2d is longitude, 3d is latitude)
GOOGLE_MAPS_EMBED_PATTERN = re.compile(
    r"google\.com/maps/embed\?pb=.*?!2d([\d.]+)!3d([\d.]+)", re.IGNORECASE
)
# Alternative pattern for different embed format where lat comes before lon
GOOGLE_MAPS_EMBED_ALT_PATTERN = re.compile(
    r"google\.com/maps/embed\?pb=.*?!3d([\d.]+).*?!2d([\d.]+)", re.IGNORECASE
)


def extract_map_iframe_location(html: str) -> Optional[V1ReraLocation]:
    """Extract lat/lon from embedded Google Maps iframe in the detail page.

    The CG RERA detail page often has a Google Maps iframe embed with coordinates
    in the URL like: https://www.google.com/maps/embed?pb=!1m14!1m12!1m3!1d...!2d81.698346!3d21.284...
    
    In Google Maps embed URLs:
    - !2d<value> is longitude
    - !3d<value> is latitude

    Args:
        html: The raw HTML content of the detail page.

    Returns:
        V1ReraLocation with source_type='map_iframe' if found, None otherwise.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Find all iframes
    iframes = soup.find_all("iframe")
    for iframe in iframes:
        src = iframe.get("src", "")
        if "google.com/maps" in src:
            # Try to extract coordinates from the embed URL
            # Format: !2d<longitude>!3d<latitude>
            match = GOOGLE_MAPS_EMBED_PATTERN.search(src)
            if match:
                lon = _parse_float(match.group(1))
                lat = _parse_float(match.group(2))
                if lat and lon and _validate_india_coordinates(lat, lon):
                    LOGGER.info("Extracted map iframe coordinates: lat=%s, lon=%s", lat, lon)
                    return V1ReraLocation(
                        source_type="map_iframe",
                        latitude=lat,
                        longitude=lon,
                        particulars="Google Maps embed from detail page",
                    )

            # Try alternative pattern (lat/lon order might be different in some URLs)
            match = GOOGLE_MAPS_EMBED_ALT_PATTERN.search(src)
            if match:
                lat = _parse_float(match.group(1))
                lon = _parse_float(match.group(2))
                if lat and lon and _validate_india_coordinates(lat, lon):
                    LOGGER.info("Extracted map iframe coordinates (alt): lat=%s, lon=%s", lat, lon)
                    return V1ReraLocation(
                        source_type="map_iframe",
                        latitude=lat,
                        longitude=lon,
                        particulars="Google Maps embed from detail page",
                    )

    LOGGER.debug("No Google Maps iframe with coordinates found")
    return None


def _validate_india_coordinates(lat: float, lon: float) -> bool:
    """Validate coordinates are roughly within India's bounding box."""
    return 6.0 <= lat <= 36.0 and 68.0 <= lon <= 98.0


def extract_amenity_locations(html: str, base_url: str = "") -> list[V1ReraLocation]:
    """Extract amenity locations with lat/lon from detail page HTML.

    The CG RERA detail page has an "Amenities Details (Only Available)" table
    with columns: From Date, To Date, Particulars, Progress Status(%), Latitude,
    Longitude, Image.

    Args:
        html: The raw HTML content of the detail page.
        base_url: Base URL for resolving relative image URLs.

    Returns:
        List of V1ReraLocation entries for each amenity with lat/lon.
    """
    soup = BeautifulSoup(html, "html.parser")
    locations: list[V1ReraLocation] = []

    # Find the amenities table by ID
    table = soup.find("table", id=AMENITIES_TABLE_ID)
    if not table:
        table = soup.find("table", id=AMENITIES_TABLE_ID_ALT)
    if not table:
        # Try to find by section heading
        table = _find_table_by_heading(soup, "Amenities Details")

    if not table:
        LOGGER.debug("No amenities table found in HTML")
        return locations

    # Parse header row to determine column indices
    header_row = table.find("tr")
    if not header_row:
        return locations

    headers = [th.get_text(" ", strip=True).lower() for th in header_row.find_all("th")]
    if not headers:
        # Some tables use td for headers
        headers = [td.get_text(" ", strip=True).lower() for td in header_row.find_all("td")]

    col_indices = _map_amenity_columns(headers)
    LOGGER.debug("Amenity table column indices: %s", col_indices)

    # Parse data rows
    data_rows = table.find_all("tr")[1:]  # Skip header row
    for row in data_rows:
        cells = row.find_all("td")
        if not cells:
            continue

        # Check for "No Data Found" row
        if len(cells) == 1:
            cell_text = cells[0].get_text(" ", strip=True).lower()
            if "no data" in cell_text or "no record" in cell_text:
                continue

        location = _parse_amenity_row(cells, col_indices, base_url)
        if location:
            locations.append(location)

    LOGGER.info("Extracted %d amenity locations from detail page", len(locations))
    return locations


def _find_table_by_heading(soup: BeautifulSoup, heading_text: str) -> Optional[Tag]:
    """Find a table near a heading containing the given text."""
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        if heading_text.lower() in heading.get_text(" ", strip=True).lower():
            # Look for table in the next siblings or parent container
            parent = heading.find_parent(["div", "section"])
            if parent:
                table = parent.find("table")
                if table:
                    return table
    return None


def _map_amenity_columns(headers: list[str]) -> dict[str, int]:
    """Map column names to indices for the amenities table."""
    column_map: dict[str, int] = {}
    aliases = {
        "from_date": {"from date", "fromdate", "start date"},
        "to_date": {"to date", "todate", "end date"},
        "particulars": {"particulars", "particular", "amenity", "name", "description"},
        "progress": {"progress status(%)", "progress status", "progress", "status(%)"},
        "latitude": {"latitude", "lat"},
        "longitude": {"longitude", "lon", "long"},
        "image": {"image", "photo", "img"},
    }

    for idx, header in enumerate(headers):
        normalized = header.strip().lower()
        for field, field_aliases in aliases.items():
            if normalized in field_aliases or any(alias in normalized for alias in field_aliases):
                if field not in column_map:
                    column_map[field] = idx
                break

    return column_map


def _get_cell_text(cells: list, index: Optional[int]) -> Optional[str]:
    """Get trimmed text from a cell by index."""
    if index is None or index >= len(cells):
        return None
    text = cells[index].get_text(" ", strip=True)
    return text if text else None


def _parse_float(value: Optional[str]) -> Optional[float]:
    """Try to parse a string as a float coordinate."""
    if not value:
        return None
    try:
        # Remove any whitespace and common formatting
        cleaned = value.strip().replace(",", ".")
        return float(cleaned)
    except ValueError:
        return None


def _extract_progress_percent(value: Optional[str]) -> Optional[float]:
    """Extract numeric progress percentage from text like '100%'."""
    if not value:
        return None
    # Extract number from strings like "100%", "75 %", "50"
    match = re.search(r"(\d+(?:\.\d+)?)", value)
    if match:
        return float(match.group(1))
    return None


def _extract_image_url(cell: Tag, base_url: str) -> Optional[str]:
    """Extract image URL from an amenity cell.

    The cell typically contains an <a> with an <img> inside.
    The actual image URL is in the img src attribute.
    """
    # Look for img tag
    img = cell.find("img")
    if img and img.has_attr("src"):
        src = img["src"].strip()
        if src:
            # Handle relative URLs
            if src.startswith("../"):
                # Resolve relative to base URL
                if base_url:
                    from urllib.parse import urljoin
                    return urljoin(base_url, src)
            return src

    # Fallback: check for anchor href (might be a link to larger image)
    anchor = cell.find("a")
    if anchor and anchor.has_attr("href"):
        href = anchor["href"].strip()
        # Skip javascript links
        if href and not href.startswith("javascript:"):
            return href

    return None


def _parse_amenity_row(
    cells: list[Tag], col_indices: dict[str, int], base_url: str
) -> Optional[V1ReraLocation]:
    """Parse a single amenity row into a V1ReraLocation."""
    lat_idx = col_indices.get("latitude")
    lon_idx = col_indices.get("longitude")

    lat = _parse_float(_get_cell_text(cells, lat_idx))
    lon = _parse_float(_get_cell_text(cells, lon_idx))

    # Skip rows without valid coordinates
    if lat is None or lon is None:
        return None

    # Validate coordinate ranges (roughly for India)
    if not _validate_india_coordinates(lat, lon):
        LOGGER.debug("Invalid coordinates outside India: lat=%s, lon=%s", lat, lon)
        return None

    particulars = _get_cell_text(cells, col_indices.get("particulars"))
    from_date = _get_cell_text(cells, col_indices.get("from_date"))
    to_date = _get_cell_text(cells, col_indices.get("to_date"))
    progress = _extract_progress_percent(_get_cell_text(cells, col_indices.get("progress")))

    image_url = None
    if "image" in col_indices and col_indices["image"] < len(cells):
        image_url = _extract_image_url(cells[col_indices["image"]], base_url)

    return V1ReraLocation(
        source_type="amenity",
        latitude=lat,
        longitude=lon,
        particulars=particulars,
        image_url=image_url,
        from_date=from_date,
        to_date=to_date,
        progress_percent=progress,
    )


def compute_centroid(locations: list[V1ReraLocation]) -> Optional[tuple[float, float]]:
    """Compute the centroid of multiple amenity locations.

    This can be used as an approximation for the project's RERA pin location
    when no explicit map marker is available.

    Returns:
        Tuple of (latitude, longitude) or None if no valid locations.
    """
    valid_locs = [(loc.latitude, loc.longitude) for loc in locations
                  if loc.latitude is not None and loc.longitude is not None]
    if not valid_locs:
        return None

    avg_lat = sum(loc[0] for loc in valid_locs) / len(valid_locs)
    avg_lon = sum(loc[1] for loc in valid_locs) / len(valid_locs)
    return (avg_lat, avg_lon)
