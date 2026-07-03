from __future__ import annotations

import json
import time
from urllib.parse import urljoin

import httpx

from app.models.category import CAR
from app.models.listing import Listing
from app.providers.html_tools import parse_html


HAMRAH_BASE_URL = "https://www.hamrah-mechanic.com"


class HamrahMechanicProvider:
    name = "hamrah-mechanic"
    categories = (CAR,)

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
        self, city: str, pages: int = 1, category: str = CAR
    ) -> list[Listing]:
        if category != CAR:
            return []
        url = f"{HAMRAH_BASE_URL}/cars-for-sale/"
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
        scripts = parse_html(html).scripts
        content = next(
            (body for attrs, body in scripts if attrs.get("id") == "__NEXT_DATA__"),
            "",
        )
        if not content:
            return []
        try:
            payload = json.loads(content)
            items = payload["props"]["pageProps"]["cars"]["list"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return []

        listings = []
        for item in items:
            item_city = str(item.get("cityNamePersian") or "")
            if item_city and item_city != city:
                continue
            external_id = str(item.get("orderId") or "")
            title = str(item.get("carNamePersian") or "").strip()
            path = str(item.get("exhibitionDetailUrl") or "")
            if not external_id or not title or not path:
                continue
            details = "، ".join(
                part
                for part in (
                    str(item.get("carTypeName") or ""),
                    str(item.get("gearBoxPersian") or ""),
                    f"{item.get('km'):,} کیلومتر" if item.get("km") is not None else "",
                )
                if part
            )
            location = "، ".join(
                part for part in (item_city or city, str(item.get("neighborhood") or "")) if part
            )
            listings.append(
                Listing(
                    source="hamrah-mechanic",
                    external_id=f"hamrah-mechanic:{external_id}",
                    title=title,
                    price=_integer(item.get("offerPrice")) or _integer(item.get("price")),
                    location=location,
                    url=urljoin(HAMRAH_BASE_URL, path),
                    description=details,
                    raw=item,
                    address=location,
                    city=item_city or city,
                    category=CAR,
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
