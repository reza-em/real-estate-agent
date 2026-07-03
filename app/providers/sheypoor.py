from __future__ import annotations

import re
import time
from urllib.parse import urljoin

import httpx

from app.core.parsing import parse_area, parse_price
from app.models.category import CAR, MOTORCYCLE, PROPERTY
from app.models.listing import Listing
from app.providers.city_slugs import city_slug
from app.providers.html_tools import parse_html


SHEYPOOR_BASE_URL = "https://www.sheypoor.com"
SHEYPOOR_CATEGORIES = {
    PROPERTY: "houses-apartments-for-sale",
    CAR: "car",
    MOTORCYCLE: "motorcycles",
}


class SheypoorProvider:
    name = "sheypoor"
    categories = tuple(SHEYPOOR_CATEGORIES)

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
        source_category = SHEYPOOR_CATEGORIES.get(category)
        if not source_category:
            return []
        base_url = f"{SHEYPOOR_BASE_URL}/s/{city_slug(city)}/{source_category}"
        results: dict[str, Listing] = {}
        for page in range(1, min(max(pages, 1), 5) + 1):
            response = self.client.get(base_url, params={"page": page} if page > 1 else None)
            response.raise_for_status()
            for listing in self._extract(response.text, city, category):
                results[listing.external_id] = listing
            if page < pages:
                time.sleep(self.request_delay)
        return list(results.values())

    @staticmethod
    def _extract(html: str, city: str, category: str) -> list[Listing]:
        parsed = parse_html(html)
        listings = []
        for href, parts in parsed.anchors.items():
            match = re.search(r"-(\d+)\.html(?:\?|$)", href)
            if not href.startswith("/v/") or not match:
                continue
            text = " ".join(dict.fromkeys(parts)).strip()
            if not text:
                continue
            listings.append(
                Listing(
                    source="sheypoor",
                    external_id=f"sheypoor:{match.group(1)}",
                    title=text[:240],
                    price=parse_price(text),
                    location=city,
                    url=urljoin(SHEYPOOR_BASE_URL, href),
                    description=text,
                    area=parse_area(text) if category == PROPERTY else None,
                    raw={"id": match.group(1), "text": text},
                    address=city,
                    city=city,
                    category=category,
                )
            )
        return listings

    def close(self) -> None:
        if self._owns_client:
            self.client.close()
