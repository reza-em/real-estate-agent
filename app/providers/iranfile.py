from __future__ import annotations

import re
import time
from urllib.parse import unquote, urljoin

import httpx

from app.core.parsing import parse_area, parse_price
from app.models.category import PROPERTY
from app.models.listing import Listing
from app.providers.html_tools import parse_html


IRANFILE_BUY_URL = "https://iranfile.ir/properties/buy"


class IranFileProvider:
    name = "iranfile"
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
        if city != "تهران":
            raise ValueError("جست‌وجوی عمومی ایران‌فایل فعلاً فقط تهران را ارائه می‌کند")
        results: dict[str, Listing] = {}
        for page in range(1, min(max(pages, 1), 5) + 1):
            response = self.client.get(
                IRANFILE_BUY_URL, params={"page": page} if page > 1 else None
            )
            response.raise_for_status()
            for listing in self._extract(response.text, city):
                results[listing.external_id] = listing
            if page < pages:
                time.sleep(self.request_delay)
        return list(results.values())

    @staticmethod
    def _extract(html: str, city: str) -> list[Listing]:
        listings = []
        for href, parts in parse_html(html).anchors.items():
            match = re.search(r"/FileDetail/(\d+)(?:/([^?#]+))?", href, re.I)
            if not match:
                continue
            text = " ".join(parts)
            slug = unquote(match.group(2) or "").replace("_", " ").strip()
            title = slug or next((part for part in parts if len(part) > 10), "ملک")
            listings.append(
                Listing(
                    source="iranfile",
                    external_id=f"iranfile:{match.group(1)}",
                    title=title[:240],
                    price=parse_price(text),
                    location=text[:240],
                    url=urljoin(IRANFILE_BUY_URL, href),
                    description=text,
                    area=parse_area(title),
                    raw={"id": match.group(1), "fields": parts},
                    address=text[:240],
                    city=city,
                    category=PROPERTY,
                )
            )
        return listings

    def close(self) -> None:
        if self._owns_client:
            self.client.close()
