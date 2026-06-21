from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass

from openai import OpenAI

from scraper import Listing


@dataclass(slots=True)
class Analysis:
    external_id: str
    score: int
    summary: str
    risks: list[str]


def basic_analysis(listings: list[Listing], max_price: int) -> list[Analysis]:
    known = [item.price for item in listings if item.price]
    cheapest = min(known, default=max_price)
    spread = max(max_price - cheapest, 1)
    output = []
    for item in listings:
        score = 35 if item.price is None else round(50 + 45 * (max_price - item.price) / spread)
        output.append(
            Analysis(
                item.external_id,
                max(0, min(score, 100)),
                "امتیاز اولیه بر اساس قیمت؛ جزئیات آگهی باید حضوری راستی‌آزمایی شود.",
                ["قیمت یا مشخصات ممکن است در متن آگهی دقیق نباشد"],
            )
        )
    return output


def analyze(listings: list[Listing], max_price: int, preferences: str = "") -> list[Analysis]:
    fallback = basic_analysis(listings, max_price)
    if not listings or not os.getenv("OPENAI_API_KEY"):
        return fallback

    candidates = sorted(
        listings, key=lambda item: item.price if item.price is not None else max_price + 1
    )[:20]
    compact = [
        {
            "id": item.external_id,
            "title": item.title,
            "price": item.price,
            "location": item.location,
            "description": item.description,
        }
        for item in candidates
    ]
    prompt = f"""
بودجه خریدار: {max_price:,} تومان
ترجیحات: {preferences or 'اعلام نشده'}
آگهی‌ها: {json.dumps(compact, ensure_ascii=False)}

آگهی‌ها را فقط با اطلاعات موجود مقایسه کن. برای هر id امتیاز ۰ تا ۱۰۰،
خلاصه کوتاه فارسی و فهرست ریسک‌ها بده. اطلاعات ناموجود را حدس نزن.
"""
    try:
        response = OpenAI().responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5.4-nano"),
            input=[
                {
                    "role": "system",
                    "content": "شما دستیار تحلیل اولیه خرید ملک هستید، نه کارشناس حقوقی یا قیمت‌گذاری رسمی.",
                },
                {"role": "user", "content": prompt},
            ],
            text={
                "format": {
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
                                        "score": {"type": "integer", "minimum": 0, "maximum": 100},
                                        "summary": {"type": "string"},
                                        "risks": {"type": "array", "items": {"type": "string"}},
                                    },
                                    "required": ["external_id", "score", "summary", "risks"],
                                    "additionalProperties": False,
                                },
                            }
                        },
                        "required": ["items"],
                        "additionalProperties": False,
                    },
                }
            },
        )
        parsed = json.loads(response.output_text)
        analyzed = {item["external_id"]: Analysis(**item) for item in parsed["items"]}
    except Exception:
        return fallback
    fallback_by_id = {item.external_id: item for item in fallback}
    return [analyzed.get(item.external_id, fallback_by_id[item.external_id]) for item in listings]


def to_dict(item: Analysis) -> dict[str, object]:
    return asdict(item)
