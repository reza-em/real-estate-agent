from __future__ import annotations

import json
import re
import time

import httpx

from app.core.parsing import parse_area
from app.models.category import PROPERTY
from app.models.listing import Listing
from app.providers.city_slugs import city_slug
from app.providers.html_tools import parse_html


class KilidProvider:
    name = "kilid"
    categories = (PROPERTY,)

    def __init__(
        self, timeout: float = 20.0, request_delay: float = 0.75, client=None
    ) -> None:
        self.request_delay = request_delay
        self.client = client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "ListingResearch/1.0 (personal-use)"},
        )
        self._owns_client = client is None

    def search(
        self, city: str, pages: int = 1, category: str = PROPERTY
    ) -> list[Listing]:
        if category != PROPERTY:
            return []
        url = f"https://kilid.com/buy-apartment/{city_slug(city)}"
        results: dict[str, Listing] = {}
        for page in range(1, min(max(pages, 1), 5) + 1):
            response = self.client.get(url, params={"page": page} if page > 1 else None)
            response.raise_for_status()
            for listing in self._extract(response.text, city):
                results[listing.external_id] = listing
            if page < pages:
                time.sleep(self.request_delay)
        return list(results.values())

    @staticmethod
    def _extract(html: str, city: str) -> list[Listing]:
        listings = []
        for attrs, content in parse_html(html).scripts:
            if attrs.get("type") != "application/ld+json" or not content:
                continue
            try:
                payload = json.loads(content)
            except json.JSONDecodeError:
                continue
            items = payload if isinstance(payload, list) else [payload]
            for item in items:
                if not isinstance(item, dict):
                    continue
                offers = item.get("offers") or {}
                url = str(offers.get("url") or "")
                match = re.search(r"/detail/(\d+)", url)
                title = str(item.get("name") or "").strip()
                if not match or not title:
                    continue
                geo = (item.get("location") or {}).get("geo") or {}
                latitude = _coordinate(geo.get("latitude"))
                longitude = _coordinate(geo.get("longitude"))
                listings.append(
                    Listing(
                        source="kilid",
                        external_id=f"kilid:{match.group(1)}",
                        title=title,
                        price=_integer(offers.get("price")),
                        location=city,
                        url=url,
                        description=title,
                        area=parse_area(title),
                        raw=item,
                        latitude=latitude,
                        longitude=longitude,
                        address=city,
                        city=city,
                        location_precision="source" if latitude is not None else "unknown",
                        category=PROPERTY,
                    )
                )
        return listings

    def close(self) -> None:
        if self._owns_client:
            self.client.close()


def _integer(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _coordinate(value: object) -> float | None:
    try:
        coordinate = float(value)
        return coordinate if coordinate else None
    except (TypeError, ValueError):
        return None
