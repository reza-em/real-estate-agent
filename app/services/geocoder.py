from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.db.repository import ListingRepository
from app.models.listing import Listing


NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
CITY_CENTERS: dict[str, tuple[float, float]] = {
    "تهران": (35.6892, 51.3890),
    "تبریز": (38.0800, 46.2919),
    "مشهد": (36.2605, 59.6168),
    "کرج": (35.8400, 50.9391),
    "شیراز": (29.5918, 52.5837),
    "اصفهان": (32.6546, 51.6680),
    "قم": (34.6416, 50.8746),
    "اهواز": (31.3183, 48.6706),
}


@dataclass(frozen=True, slots=True)
class GeocodeResult:
    latitude: float
    longitude: float
    address: str | None
    precision: str


class GeocoderService:
    def __init__(
        self,
        repository: ListingRepository,
        client: Any | None = None,
        max_live_requests: int = 3,
        request_interval: float = 1.05,
        live_enabled: bool | None = None,
        city_centers: dict[str, tuple[float, float]] | None = None,
    ) -> None:
        self.repository = repository
        self.max_live_requests = max(0, max_live_requests)
        self.request_interval = max(0.0, request_interval)
        self.city_centers = {**CITY_CENTERS, **(city_centers or {})}
        self.live_enabled = (
            os.getenv("GEOCODING_ENABLED", "true").lower() not in {"0", "false", "no"}
            if live_enabled is None
            else live_enabled
        )
        self.client = client or httpx.Client(
            timeout=6.0,
            headers={
                "User-Agent": os.getenv(
                    "GEOCODER_USER_AGENT",
                    "real-estate-agent/0.3 (https://github.com/reza-em/real-estate-agent)",
                )
            },
        )
        self._owns_client = client is None

    def enrich(self, listings: list[Listing], selected_city: str) -> list[Listing]:
        live_requests = 0
        live_failed = False
        resolved: dict[str, GeocodeResult] = {}

        for listing in listings:
            if listing.has_coordinates:
                continue
            listing.city = listing.city or selected_city
            listing.address = listing.address or listing.location or None
            query = self._query(listing, selected_city)

            result = resolved.get(query) or self._cached(query)
            if result is None and self.live_enabled and not live_failed:
                if live_requests < self.max_live_requests:
                    if live_requests:
                        time.sleep(self.request_interval)
                    try:
                        result = self._geocode_live(query)
                    except (httpx.HTTPError, ValueError):
                        live_failed = True
                    live_requests += 1

            if result is None:
                result = self._fallback(query, selected_city)

            resolved[query] = result
            self.repository.save_geocode(
                query,
                result.latitude,
                result.longitude,
                result.address,
                result.precision,
            )
            listing.latitude = result.latitude
            listing.longitude = result.longitude
            listing.address = result.address or listing.address
            listing.location_precision = result.precision
        return listings

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def _cached(self, query: str) -> GeocodeResult | None:
        cached = self.repository.get_cached_geocode(query)
        return GeocodeResult(*cached) if cached else None

    def _geocode_live(self, query: str) -> GeocodeResult | None:
        response = self.client.get(
            NOMINATIM_SEARCH_URL,
            params={
                "q": query,
                "format": "jsonv2",
                "limit": 1,
                "countrycodes": "ir",
                "accept-language": "fa",
            },
        )
        response.raise_for_status()
        payload = response.json()
        if not payload:
            return None
        item = payload[0]
        return GeocodeResult(
            latitude=float(item["lat"]),
            longitude=float(item["lon"]),
            address=str(item.get("display_name") or query),
            precision="geocoded",
        )

    @staticmethod
    def _query(listing: Listing, selected_city: str) -> str:
        location = listing.address or listing.location or listing.city or selected_city
        if selected_city not in location:
            location = f"{location}، {selected_city}"
        return f"{location}، ایران"

    def _fallback(self, query: str, city: str) -> GeocodeResult:
        center_lat, center_lon = self.city_centers.get(
            city, self.city_centers["تهران"]
        )
        digest = hashlib.sha256(query.encode("utf-8")).digest()
        lat_offset = (int.from_bytes(digest[:2], "big") / 65535 - 0.5) * 0.07
        lon_offset = (int.from_bytes(digest[2:4], "big") / 65535 - 0.5) * 0.07
        return GeocodeResult(
            center_lat + lat_offset,
            center_lon + lon_offset,
            None,
            "approximate",
        )
