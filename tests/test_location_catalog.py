from datetime import timedelta
from pathlib import Path

import httpx

from app.db.location_repository import LocationCatalogRepository
from app.services.location_catalog import LocationCatalogService


def payload():
    return {
        "cities": [
            {
                "id": 1,
                "name": "تهران",
                "parent": 904,
                "centroid": {"latitude": 35.7, "longitude": 51.4},
            },
            {
                "id": 101,
                "name": "پردیس",
                "parent": 904,
                "centroid": {"latitude": 35.74, "longitude": 51.78},
            },
            {
                "id": 6,
                "name": "شیراز",
                "parent": 898,
                "centroid": {"latitude": 29.59, "longitude": 52.58},
            },
        ]
    }


def test_catalog_groups_cities_by_province_and_saves_cache(tmp_path: Path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload())

    path = tmp_path / "places.db"
    client = httpx.Client(transport=httpx.MockTransport(handler))
    catalog = LocationCatalogService(
        LocationCatalogRepository(path), client=client, cache_ttl=timedelta(0)
    )
    grouped = catalog.by_province()
    assert grouped["تهران"] == sorted(["پردیس", "تهران"])
    assert grouped["فارس"] == ["شیراز"]
    assert catalog.city_ids["پردیس"] == "101"
    assert catalog.city_centers["شیراز"] == (29.59, 52.58)
    client.close()


def test_catalog_uses_fresh_cache_without_network(tmp_path: Path):
    path = tmp_path / "places.db"
    repository = LocationCatalogRepository(path)
    repository.save(payload())

    def fail_if_called(request: httpx.Request) -> httpx.Response:
        raise AssertionError("network should not be called")

    client = httpx.Client(transport=httpx.MockTransport(fail_if_called))
    catalog = LocationCatalogService(repository, client=client)
    assert catalog.province_for_city("پردیس") == "تهران"
    client.close()
