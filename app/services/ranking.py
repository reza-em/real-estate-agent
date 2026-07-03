from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from app.models.analysis import Analysis
from app.models.category import category_label
from app.models.listing import Listing


class RankingService:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.4-nano")
        self._client = client

    @property
    def ai_available(self) -> bool:
        return bool(self.api_key)

    def rank(
        self,
        listings: list[Listing],
        max_price: int,
        preferences: str = "",
        use_ai: bool = True,
    ) -> list[Analysis]:
        fallback = self._basic_rank(listings, max_price)
        if not listings or not use_ai or not self.ai_available:
            return fallback

        try:
            ai_results = self._rank_with_ai(listings, max_price, preferences)
        except Exception:
            return fallback

        fallback_by_id = {item.external_id: item for item in fallback}
        ai_by_id = {item.external_id: item for item in ai_results}
        return [
            ai_by_id.get(listing.external_id, fallback_by_id[listing.external_id])
            for listing in listings
        ]

    @staticmethod
    def _basic_rank(listings: list[Listing], max_price: int) -> list[Analysis]:
        known_prices = [listing.price for listing in listings if listing.price]
        cheapest = min(known_prices, default=max_price)
        spread = max(max_price - cheapest, 1)
        results = []
        for listing in listings:
            score = (
                35
                if listing.price is None
                else round(50 + 45 * (max_price - listing.price) / spread)
            )
            results.append(
                Analysis(
                    external_id=listing.external_id,
                    score=max(0, min(score, 100)),
                    summary="امتیاز اولیه بر اساس قیمت؛ مشخصات آگهی نیازمند راستی‌آزمایی است.",
                    risks=["قیمت و مشخصات باید پیش از معامله بررسی شوند"],
                )
            )
        return results

    def _rank_with_ai(
        self, listings: list[Listing], max_price: int, preferences: str
    ) -> list[Analysis]:
        candidates = sorted(
            listings,
            key=lambda listing: (
                listing.price if listing.price is not None else max_price + 1
            ),
        )[:20]
        compact = [
            {
                "id": listing.external_id,
                "title": listing.title,
                "price": listing.price,
                "area": listing.area,
                "location": listing.location,
                "description": listing.description,
                "category": category_label(listing.category),
            }
            for listing in candidates
        ]
        prompt = f"""
بودجه خریدار: {max_price:,} تومان
ترجیحات: {preferences or 'اعلام نشده'}
آگهی‌ها: {json.dumps(compact, ensure_ascii=False)}

آگهی‌ها را فقط با اطلاعات موجود مقایسه کن. برای هر id امتیاز ۰ تا ۱۰۰،
خلاصه کوتاه فارسی و فهرست ریسک‌ها بده. اطلاعات ناموجود را حدس نزن.
"""
        client = self._client or OpenAI(api_key=self.api_key)
        response = client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": "شما دستیار تحلیل اولیه خرید ملک و وسیله نقلیه هستید، نه کارشناس رسمی حقوقی، فنی یا قیمت‌گذاری.",
                },
                {"role": "user", "content": prompt},
            ],
            text={"format": self._response_schema()},
        )
        parsed = json.loads(response.output_text)
        return [Analysis(**item) for item in parsed["items"]]

    @staticmethod
    def _response_schema() -> dict[str, Any]:
        return {
            "type": "json_schema",
            "name": "listing_analysis",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "external_id": {"type": "string"},
                                "score": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 100,
                                },
                                "summary": {"type": "string"},
                                "risks": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": [
                                "external_id",
                                "score",
                                "summary",
                                "risks",
                            ],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["items"],
                "additionalProperties": False,
            },
        }
