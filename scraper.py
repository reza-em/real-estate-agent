from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

import httpx


DIVAR_SEARCH_URL = "https://api.divar.ir/v8/postlist/w/search"
DIVAR_BUY_CATEGORIES = ("apartment-sell", "house-villa-sell")
CITY_IDS = {
    "تهران": "1",
    "تبریز": "2",
    "مشهد": "3",
    "کرج": "4",
    "شیراز": "6",
    "اصفهان": "7",
    "قم": "8",
    "اهواز": "10",
}
PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


@dataclass(slots=True)
class Listing:
    source: str
    external_id: str
    title: str
    price: int | None
    location: str
    url: str
    description: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


def parse_price(value: str | None) -> int | None:
    if not value or any(word in value for word in ("توافق", "تماس")):
        return None
    normalized = value.translate(PERSIAN_DIGITS).replace("٬", "").replace(",", "")
    numbers = re.findall(r"\d+(?:\.\d+)?", normalized)
    if not numbers:
        return None
    price = max(float(number) for number in numbers)
    if "میلیارد" in value:
        price *= 1_000_000_000
    elif "میلیون" in value:
        price *= 1_000_000
    return int(price)


class DivarProvider:
    """A small, defensive client for Divar's public search response.

    This endpoint is not a guaranteed partner API. Keep request volume low and
    replace this provider with an approved API integration for production use.
    """

    def __init__(self, timeout: float = 20.0) -> None:
        self.client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "RealEstateResearch/0.1 (personal-use)"},
        )

    def search(self, city: str, max_price: int, pages: int = 1) -> list[Listing]:
        if city not in CITY_IDS:
            raise ValueError(f"شهر پشتیبانی نمی‌شود: {city}")
        results: dict[str, Listing] = {}
        page_count = min(max(pages, 1), 5)
        for category in DIVAR_BUY_CATEGORIES:
            for page in range(1, page_count + 1):
                response = self.client.post(
                    DIVAR_SEARCH_URL,
                    json=self._payload(CITY_IDS[city], page, category),
                )
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    detail = response.text.strip()[:500]
                    raise RuntimeError(
                        f"دیوار پاسخ {response.status_code} داد: {detail}"
                    ) from exc
                for item in self._extract(response.json()):
                    if item.price is not None and item.price <= max_price:
                        results[item.external_id] = item
                if page < page_count:
                    time.sleep(1.0)
            time.sleep(1.0)
        return list(results.values())

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
                    "data": {
                        "category": {"str": {"value": category}}
                    }
                },
                "server_payload": {
                    "@type": "type.googleapis.com/widgets.SearchData.ServerPayload",
                    "additional_form_data": {
                        "data": {"sort": {"str": {"value": "sort_date"}}}
                    },
                },
            },
        }

    @staticmethod
    def _extract(payload: dict[str, Any]) -> list[Listing]:
        widgets = payload.get("list_widgets") or payload.get("list_web_widgets") or []
        listings: list[Listing] = []
        for widget in widgets:
            if widget.get("widget_type") != "POST_ROW":
                continue
            data = widget.get("data") or {}
            action_payload = (data.get("action") or {}).get("payload") or {}
            web_info = action_payload.get("web_info") or {}
            token = str(data.get("token") or action_payload.get("token") or "")
            title = str(data.get("title") or "").strip()
            if not token or not title:
                continue
            price_text = " ".join(
                str(data.get(key) or "")
                for key in (
                    "middle_description_text",
                    "middle_description",
                    "bottom_description_text",
                    "bottom_description",
                )
            )
            location_parts = [
                str(web_info.get("city_persian") or ""),
                str(web_info.get("district_persian") or ""),
            ]
            location = "، ".join(part for part in location_parts if part)
            if not location:
                location = str(data.get("top_description") or "")
            listings.append(
                Listing(
                    source="divar",
                    external_id=token,
                    title=title,
                    price=parse_price(price_text),
                    location=location,
                    url=f"https://divar.ir/v/-/{token}",
                    description=price_text.strip(),
                    raw=data,
                )
            )
        return listings
