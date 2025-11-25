"""Utilities for producing consistent, geocoding-ready address strings."""
from __future__ import annotations

from dataclasses import dataclass


_STATE_CODE_TO_NAME = {
    "CG": "Chhattisgarh",
}


@dataclass(slots=True)
class AddressParts:
    """Structured representation of address components."""

    address_line: str | None = None
    village_or_locality: str | None = None
    tehsil: str | None = None
    district: str | None = None
    state: str | None = None
    state_code: str | None = None
    pincode: str | None = None
    country: str | None = "India"


@dataclass(slots=True)
class AddressNormalizationResult:
    """Result from :func:`normalize_address` with confidence hints."""

    normalized_address: str
    components_used: list[str]
    missing_components: list[str]

    @property
    def is_low_confidence(self) -> bool:
        """Flag obviously weak addresses for downstream consumers.

        The heuristic considers addresses weak when fewer than three components
        are present or when no district is available alongside a locality-level
        component (address line, village/locality, or tehsil).
        """

        has_locality = any(
            component in self.components_used
            for component in ("address_line", "village_or_locality", "tehsil")
        )
        has_district = "district" in self.components_used
        return len(self.components_used) < 3 or not (has_locality and has_district)


def _clean_component(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = " ".join(value.replace(",", " ").split())
    return cleaned or None


def _normalize_district(value: str | None) -> str | None:
    cleaned = _clean_component(value)
    if not cleaned:
        return None

    lowered = cleaned.lower()
    for prefix in ("district", "dist.", "dist ", "dist"):
        if lowered.startswith(prefix):
            remainder = cleaned[len(prefix) :].lstrip(" .-")
            return f"District {remainder}" if remainder else "District"
    return cleaned


def _normalize_tehsil(value: str | None) -> str | None:
    cleaned = _clean_component(value)
    if not cleaned:
        return None

    # Normalize common abbreviation "Tah"/"Tahsil"
    lowered = cleaned.lower()
    for prefix in ("tahsildar", "tahsil", "tehsil", "tah.", "tah"):
        if lowered.startswith(prefix):
            remainder = cleaned[len(prefix) :].lstrip(" .-")
            return f"Tehsil {remainder}" if remainder else "Tehsil"
    return cleaned


def _resolve_state(parts: AddressParts) -> str | None:
    return _clean_component(parts.state) or _STATE_CODE_TO_NAME.get(
        (parts.state_code or "").upper() or None
    )


def normalize_address(parts: AddressParts) -> AddressNormalizationResult:
    """Create a comma-delimited normalized address string.

    Components are ordered as: address line, village/locality, tehsil, district,
    state, pincode, country. Missing or empty values are skipped. Abbreviations
    like "Dist." and "Tah." are expanded to aid geocoding. Excess whitespace and
    stray commas are removed.
    """

    state_value = _resolve_state(parts)

    ordered_components: list[tuple[str, str | None]] = [
        ("address_line", _clean_component(parts.address_line)),
        ("village_or_locality", _clean_component(parts.village_or_locality)),
        ("tehsil", _normalize_tehsil(parts.tehsil)),
        ("district", _normalize_district(parts.district)),
        ("state", state_value),
        ("pincode", _clean_component(parts.pincode)),
        ("country", _clean_component(parts.country)),
    ]

    components_used: list[str] = []
    missing_components: list[str] = []
    rendered: list[str] = []

    for name, value in ordered_components:
        if value:
            rendered.append(value)
            components_used.append(name)
        else:
            missing_components.append(name)

    normalized_address = ", ".join(rendered)
    return AddressNormalizationResult(
        normalized_address=normalized_address,
        components_used=components_used,
        missing_components=missing_components,
    )


def generate_geocoding_candidates(parts: AddressParts) -> list[str]:
    """Generate a list of address strings with decreasing specificity.

    This is useful for fallback geocoding when the full address fails.
    Strategies:
    1. Full address (Address Line + Locality + Tehsil + District + State + Pincode)
    2. Locality level (Locality + Tehsil + District + State + Pincode)
    3. Tehsil level (Tehsil + District + State)
    4. District level (District + State)
    """
    candidates = []
    seen = set()

    # Helper to build and add unique candidate
    def add_candidate(current_parts: AddressParts):
        result = normalize_address(current_parts)
        addr = result.normalized_address
        if addr and addr not in seen:
            candidates.append(addr)
            seen.add(addr)

    # 1. Full address
    add_candidate(parts)

    # 2. Drop address_line (often contains specific landmarks/plot numbers that confuse geocoders)
    if parts.address_line:
        parts_no_line = dataclass_replace(parts, address_line=None)
        add_candidate(parts_no_line)

    # 3. Drop village_or_locality (keep tehsil/district)
    if parts.village_or_locality:
        parts_no_loc = dataclass_replace(parts, address_line=None, village_or_locality=None)
        add_candidate(parts_no_loc)

    # 4. Drop tehsil (keep district)
    if parts.tehsil:
        parts_district = dataclass_replace(
            parts, 
            address_line=None, 
            village_or_locality=None, 
            tehsil=None
        )
        add_candidate(parts_district)

    return candidates


# Helper for dataclass replacement (available in stdlib dataclasses but explicit here for clarity/compat)
from dataclasses import replace as dataclass_replace


__all__ = [
    "AddressNormalizationResult",
    "AddressParts",
    "normalize_address",
    "generate_geocoding_candidates",
]
