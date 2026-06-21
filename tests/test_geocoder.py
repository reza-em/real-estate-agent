from pathlib import Path

import httpx

from app.db.repository import ListingRepository
from app.models.listing import Listing
from app.services.geocoder import GeocoderService


def make_listing(external_id: str, location: str = "تهران، پونک") -> Listing:
    return Listing(
        source="test",
        external_id=external_id,
        title="آپارتمان ۸۰ متری",
        price=8_000_000_000,
        location=location,
        url="https://example.com",
        city="تهران",
        address=location,
    )


def test_geocoder_uses_live_result_and_reuses_query(tmp_path: Path):
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json=[{"lat": "35.76", "lon": "51.31", "display_name": "پونک، تهران"}],
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    service = GeocoderService(
        ListingRepository(tmp_path / "geo.db"),
        client=client,
        request_interval=0,
    )
    listings = service.enrich([make_listing("a"), make_listing("b")], "تهران")
    assert calls == 1
    assert all(item.latitude == 35.76 for item in listings)
    assert all(item.location_precision == "geocoded" for item in listings)
    client.close()


def test_geocoder_falls_back_without_crashing(tmp_path: Path):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    service = GeocoderService(
        ListingRepository(tmp_path / "fallback.db"),
        client=client,
        request_interval=0,
    )
    listings = service.enrich(
        [make_listing("a"), make_listing("b", "تهران، ونک")], "تهران"
    )
    assert all(item.has_coordinates for item in listings)
    assert all(item.location_precision == "approximate" for item in listings)
    client.close()
