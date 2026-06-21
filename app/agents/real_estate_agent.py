from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable
from typing import Any

from openai import OpenAI

from app.core.parsing import normalize_digits
from app.memory.service import UserMemoryService
from app.models.agent import AgentResponse, ParsedAgentQuery
from app.models.memory import UserProfile
from app.models.search import SearchCriteria
from app.providers.divar import CITY_IDS
from app.services.decision_engine import DecisionEngine
from app.services.search import SearchService


CITY_ALIASES = {
    "tehran": "تهران",
    "tabriz": "تبریز",
    "mashhad": "مشهد",
    "karaj": "کرج",
    "shiraz": "شیراز",
    "isfahan": "اصفهان",
    "esfahan": "اصفهان",
    "qom": "قم",
    "ahvaz": "اهواز",
}


class AgentQueryParser:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: Any | None = None,
        city_names: Iterable[str] | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.4-nano")
        self._client = client
        self.city_names = tuple(city_names or CITY_IDS)

    def parse(self, text: str, profile: UserProfile, pages: int = 1) -> ParsedAgentQuery:
        if self.api_key:
            try:
                return self._parse_with_ai(text, profile, pages)
            except Exception:
                pass
        return self._parse_with_rules(text, profile, pages)

    def _parse_with_ai(
        self, text: str, profile: UserProfile, pages: int
    ) -> ParsedAgentQuery:
        defaults = {
            "city": profile.preferred_cities[-1] if profile.preferred_cities else "تهران",
            "budget": profile.budget or 10_000_000_000,
            "min_area": profile.min_area,
            "preferences": profile.preferences,
        }
        client = self._client or OpenAI(api_key=self.api_key)
        response = client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "درخواست خرید ملک را به فیلتر ساختاری تبدیل کن. "
                        "مبالغ را همیشه به تومان برگردان و اطلاعات ناموجود را از defaults بردار."
                    ),
                },
                {
                    "role": "user",
                    "content": f"defaults={json.dumps(defaults, ensure_ascii=False)}\nquery={text}",
                },
            ],
            text={"format": self._schema()},
        )
        data = json.loads(response.output_text)
        criteria = self._validated_criteria(data, text, pages)
        return ParsedAgentQuery(criteria=criteria, parser="openai")

    def _parse_with_rules(
        self, text: str, profile: UserProfile, pages: int
    ) -> ParsedAgentQuery:
        normalized = normalize_digits(text).lower().replace("٬", "").replace(",", "")
        city = self._find_city(normalized, profile)
        budget = self._find_budget(normalized) or profile.budget or 10_000_000_000
        min_area = self._find_area(normalized)
        if min_area is None:
            min_area = profile.min_area
        criteria = SearchCriteria(
            city=city,
            max_price=budget,
            min_area=max(0, min_area),
            pages=min(max(pages, 1), 5),
            preferences=text.strip() or profile.preferences,
            use_ai=False,
        )
        return ParsedAgentQuery(criteria=criteria, parser="rules")

    def _find_city(self, text: str, profile: UserProfile) -> str:
        for city in sorted(self.city_names, key=len, reverse=True):
            if city in text:
                return city
        for alias, city in CITY_ALIASES.items():
            if re.search(rf"\b{re.escape(alias)}\b", text):
                return city
        return profile.preferred_cities[-1] if profile.preferred_cities else "تهران"

    @staticmethod
    def _find_budget(text: str) -> int | None:
        patterns = (
            (r"(\d+(?:\.\d+)?)\s*(?:میلیارد|billion|bn)\b", 1_000_000_000),
            (r"(\d+(?:\.\d+)?)\s*(?:میلیون|million|mn)\b", 1_000_000),
            (r"(?:بودجه|تا|زیر|under|max(?:imum)?)\D{0,12}(\d{6,15})", 1),
        )
        for pattern, multiplier in patterns:
            match = re.search(pattern, text)
            if match:
                return int(float(match.group(1)) * multiplier)
        return None

    @staticmethod
    def _find_area(text: str) -> int | None:
        patterns = (
            r"(?:حداقل|کمتر از|at least|minimum|min)\s*(\d{2,4})\s*(?:متر|m2|m²|m)\b",
            r"(\d{2,4})\s*(?:متر|m2|m²|m)\b",
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None

    def _validated_criteria(
        self, data: dict[str, Any], original_text: str, pages: int
    ) -> SearchCriteria:
        city = str(data["city"])
        if city not in self.city_names:
            city = "تهران"
        return SearchCriteria(
            city=city,
            max_price=max(100_000_000, int(data["budget"])),
            min_area=max(0, int(data["min_area"])),
            pages=min(max(pages, 1), 5),
            preferences=str(data.get("preferences") or original_text),
            use_ai=False,
        )

    @staticmethod
    def _schema() -> dict[str, Any]:
        return {
            "type": "json_schema",
            "name": "real_estate_query",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "budget": {"type": "integer", "minimum": 100_000_000},
                    "min_area": {"type": "integer", "minimum": 0},
                    "preferences": {"type": "string"},
                },
                "required": ["city", "budget", "min_area", "preferences"],
                "additionalProperties": False,
            },
        }


class RealEstateAgent:
    def __init__(
        self,
        search_service: SearchService,
        memory: UserMemoryService,
        parser: AgentQueryParser | None = None,
        decision_engine: DecisionEngine | None = None,
    ) -> None:
        self.search_service = search_service
        self.memory = memory
        self.parser = parser or AgentQueryParser()
        self.decision_engine = decision_engine or DecisionEngine()

    def ask(self, user_id: str, text: str, pages: int = 1) -> AgentResponse:
        profile = self.memory.profile(user_id)
        parsed = self.parser.parse(text, profile, pages)
        self.memory.remember_search(
            user_id, parsed.criteria, mode="agent", raw_query=text
        )
        result = self.search_service.search(parsed.criteria)
        updated_profile = self.memory.profile(user_id)
        result.items = self.decision_engine.rank(
            result.items, parsed.criteria, updated_profile
        )
        recommendations = result.items[:3]
        self.memory.remember_recommendations(
            user_id,
            [item.listing.external_id for item in recommendations],
            parsed.parser,
        )
        return AgentResponse(parsed, result, recommendations)
