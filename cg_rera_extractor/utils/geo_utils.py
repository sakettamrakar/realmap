"""
Geospatial utility functions for RealMap.
Part of Phase 2: Enhanced Geospatial Intelligence.
"""
import math
from typing import NamedTuple

class Coordinates(NamedTuple):
    lat: float
    lon: float

def haversine_distance(coord1: Coordinates, coord2: Coordinates) -> float:
    """
    Calculate the great-circle distance between two points on the Earth 
    using the Haversine formula. Returns distance in kilometers.
    """
    R = 6371.0  # Earth's radius in kilometers

    lat1, lon1 = math.radians(coord1.lat), math.radians(coord1.lon)
    lat2, lon2 = math.radians(coord2.lat), math.radians(coord2.lon)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def is_within_radius(coord1: Coordinates, coord2: Coordinates, radius_km: float) -> bool:
    """Check if two points are within a specific radius."""
    return haversine_distance(coord1, coord2) <= radius_km
