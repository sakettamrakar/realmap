from pathlib import Path

from cg_rera_extractor.geo import GeocodeCache, GeocodeResult, GeocodingClient


class FakeProvider:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def geocode(self, normalized_address: str) -> GeocodeResult:
        self.calls.append(normalized_address)
        return GeocodeResult(
            lat=1.23,
            lon=4.56,
            formatted_address="Fake St",
            geo_precision="test",
            geo_source=self.name,
            raw={"value": normalized_address},
        )


def test_geocode_cache_roundtrip(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.sqlite"
    cache = GeocodeCache(cache_path)

    result = GeocodeResult(1.0, 2.0, "Test", "approx", "fake", raw={"ok": True})
    cache.store("addr", result)

    cached = cache.fetch("addr")
    assert cached is not None
    assert cached.lat == 1.0
    assert cached.geo_source == "fake"


def test_geocoding_client_uses_cache(tmp_path: Path) -> None:
    cache = GeocodeCache(tmp_path / "cache.sqlite")
    provider = FakeProvider()
    client = GeocodingClient(provider, cache)

    first = client.geocode("somewhere")
    second = client.geocode("somewhere")

    assert first is not None
    assert second is not None
    assert provider.calls == ["somewhere"]
