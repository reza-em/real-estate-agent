from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

import httpx

from app.core.parsing import parse_area, parse_price
from app.models.listing import Listing
from app.models.category import CAR, MOTORCYCLE, PROPERTY


DIVAR_SEARCH_URL = "https://api.divar.ir/v8/postlist/w/search"
DIVAR_BUY_CATEGORIES = ("apartment-sell", "house-villa-sell")
DIVAR_CATEGORIES = {
    PROPERTY: DIVAR_BUY_CATEGORIES,
    CAR: ("light",),
    MOTORCYCLE: ("motorcycles",),
}
from app.services.location_catalog import FALLBACK_CAPITALS


CITY_IDS = {name: str(city_id) for city_id, name, _, _, _ in FALLBACK_CAPITALS}


class DivarProvider:
    """Fetches and normalizes Divar search results."""

    name = "divar"
    categories = tuple(DIVAR_CATEGORIES)

    def __init__(
        self,
        timeout: float = 20.0,
        request_delay: float = 1.0,
        city_ids: Mapping[str, str] | None = None,
    ) -> None:
        self.request_delay = request_delay
        self.city_ids = dict(city_ids or CITY_IDS)
        self.client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "RealEstateResearch/0.2 (personal-use)"},
        )

    def search(
        self, city: str, pages: int = 1, category: str = PROPERTY
    ) -> list[Listing]:
        if city not in self.city_ids:
            raise ValueError(f"شهر پشتیبانی نمی‌شود: {city}")
        if category not in DIVAR_CATEGORIES:
            return []

        results: dict[str, Listing] = {}
        page_count = min(max(pages, 1), 5)
        source_categories = DIVAR_CATEGORIES[category]
        for category_index, source_category in enumerate(source_categories):
            for page in range(1, page_count + 1):
                response = self.client.post(
                    DIVAR_SEARCH_URL,
                    json=self._payload(self.city_ids[city], page, source_category),
                )
                self._raise_for_status(response)
                for listing in self._extract(response.json(), category):
                    results[listing.external_id] = listing
                if page < page_count:
                    time.sleep(self.request_delay)
            if category_index < len(source_categories) - 1:
                time.sleep(self.request_delay)
        return list(results.values())

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> DivarProvider:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = response.text.strip()[:500]
            raise RuntimeError(
                f"دیوار پاسخ {response.status_code} داد: {detail}"
            ) from exc

    @staticmethod
    def _payload(
        city_id: str, page: int, category: str = DIVAR_BUY_CATEGORIES[0]
    ) -> dict[str, Any]:
        return {
            "city_ids": [city_id],
            "pagination_data": {
                "@type": "type.googleapis.com/post_list.PaginationData",
                "page": page,
                "layer_page": page,
            },
            "search_data": {
                "form_data": {
                    "data": {"category": {"str": {"value": category}}}
                },
                "server_payload": {
                    "@type": "type.googleapis.com/widgets.SearchData.ServerPayload",
                    "additional_form_data": {
                        "data": {"sort": {"str": {"value": "sort_date"}}}
                    },
                },
            },
        }

    @classmethod
    def _extract(
        cls, payload: dict[str, Any], category: str = PROPERTY
    ) -> list[Listing]:
        widgets = payload.get("list_widgets") or payload.get("list_web_widgets") or []
        listings: list[Listing] = []
        for widget in widgets:
            if widget.get("widget_type") != "POST_ROW":
                continue
            listing = cls._parse_widget(widget.get("data") or {}, category)
            if listing:
                listings.append(listing)
        return listings

    @staticmethod
    def _parse_widget(
        data: dict[str, Any], category: str = PROPERTY
    ) -> Listing | None:
        action_payload = (data.get("action") or {}).get("payload") or {}
        web_info = action_payload.get("web_info") or {}
        token = str(data.get("token") or action_payload.get("token") or "")
        title = str(data.get("title") or "").strip()
        if not token or not title:
            return None

        price_text = " ".join(
            str(data.get(key) or "")
            for key in (
                "middle_description_text",
                "middle_description",
                "bottom_description_text",
                "bottom_description",
            )
        ).strip()
        location_parts = (
            str(web_info.get("city_persian") or ""),
            str(web_info.get("district_persian") or ""),
        )
        city = location_parts[0]
        location = "، ".join(part for part in location_parts if part)
        if not location:
            location = str(data.get("top_description") or "")

        return Listing(
            source="divar",
            external_id=token,
            title=title,
            price=parse_price(price_text),
            location=location,
            url=f"https://divar.ir/v/-/{token}",
            description=price_text,
            area=parse_area(title) if category == PROPERTY else None,
            raw=data,
            address=location or None,
            city=city,
            category=category,
        )
