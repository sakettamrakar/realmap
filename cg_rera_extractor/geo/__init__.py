"""Geocoding interfaces and services for CG RERA projects."""

from .address_normalizer import (
    AddressNormalizationResult,
    AddressParts,
    normalize_address,
)
from .interface import Geocoder, GeocodingStatus, NoopGeocoder
from .service import geocode_missing_projects
from .geocoder import (
    GeocodeCache,
    GeocodeResult,
    GeocodingClient,
    GeocodingProvider,
    GoogleGeocodingProvider,
    NominatimGeocodingProvider,
    RateLimiter,
    build_geocoding_client,
)

__all__ = [
    "AddressNormalizationResult",
    "AddressParts",
    "Geocoder",
    "GeocodingStatus",
    "normalize_address",
    "NoopGeocoder",
    "geocode_missing_projects",
    "GeocodeCache",
    "GeocodeResult",
    "GeocodingClient",
    "GeocodingProvider",
    "GoogleGeocodingProvider",
    "NominatimGeocodingProvider",
    "RateLimiter",
    "build_geocoding_client",
]
