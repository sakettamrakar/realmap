"""Geocoding interfaces and services for CG RERA projects."""

from .address_normalizer import (
    AddressNormalizationResult,
    AddressParts,
    normalize_address,
)
from .interface import Geocoder, GeocodingStatus, NoopGeocoder
from .service import geocode_missing_projects

__all__ = [
    "AddressNormalizationResult",
    "AddressParts",
    "Geocoder",
    "GeocodingStatus",
    "normalize_address",
    "NoopGeocoder",
    "geocode_missing_projects",
]
