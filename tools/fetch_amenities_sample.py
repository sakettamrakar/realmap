"""CLI helper to fetch amenities via provider + cache for manual inspection."""
from __future__ import annotations

import argparse
import logging

from cg_rera_extractor.amenities import AmenityCache, get_provider_from_config
from cg_rera_extractor.amenities.cache import haversine_distance_km
from cg_rera_extractor.config.loader import load_config
from cg_rera_extractor.db import apply_migrations, get_engine, get_session_local

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch amenities around a coordinate")
    parser.add_argument("lat", type=float, help="Latitude in decimal degrees")
    parser.add_argument("lon", type=float, help="Longitude in decimal degrees")
    parser.add_argument("amenity_type", type=str, help="Normalized amenity type")
    parser.add_argument("radius_km", type=float, help="Search radius in kilometers")
    parser.add_argument(
        "--config",
        type=str,
        default="config.example.yaml",
        help="Path to YAML config (defaults to config.example.yaml)",
    )
    parser.add_argument(
        "--freshness-days",
        type=int,
        default=60,
        help="Use cached POIs seen within this many days",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    engine = get_engine(config.db)
    apply_migrations(engine)
    SessionLocal = get_session_local(engine)

    provider = get_provider_from_config(config.amenities)
    cache = AmenityCache(
        provider=provider,
        session_factory=SessionLocal,
        freshness_days=args.freshness_days,
    )

    amenities = cache.fetch_amenities(
        lat=args.lat,
        lon=args.lon,
        amenity_type=args.amenity_type,
        radius_km=args.radius_km,
    )

    if not amenities:
        logger.info("No amenities found for %s within %.2f km", args.amenity_type, args.radius_km)
        return

    amenities_with_distance = [
        (
            haversine_distance_km(args.lat, args.lon, amenity.lat, amenity.lon),
            amenity,
        )
        for amenity in amenities
    ]

    amenities_with_distance.sort(key=lambda item: item[0])
    logger.info("Fetched %d amenities via provider '%s'", len(amenities), provider.name)
    for distance, amenity in amenities_with_distance[:5]:
        logger.info(
            "- %s (%.2f km) [%s]",
            amenity.name or "<unnamed>",
            distance,
            amenity.formatted_address or "no address",
        )

if __name__ == "__main__":
    main()
