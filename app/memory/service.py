from __future__ import annotations

from app.memory.repository import MemoryRepository
from app.models.listing import Listing
from app.models.memory import UserProfile
from app.models.search import SearchCriteria


class UserMemoryService:
    def __init__(self, repository: MemoryRepository | None = None) -> None:
        self.repository = repository or MemoryRepository()

    @staticmethod
    def normalize_user_id(user_id: str) -> str:
        normalized = user_id.strip()[:64]
        return normalized or "default"

    def profile(self, user_id: str) -> UserProfile:
        return self.repository.get_profile(self.normalize_user_id(user_id))

    def remember_search(
        self,
        user_id: str,
        criteria: SearchCriteria,
        mode: str,
        raw_query: str = "",
    ) -> UserProfile:
        user_id = self.normalize_user_id(user_id)
        profile = self.repository.get_profile(user_id)
        profile.budget = criteria.max_price
        profile.min_area = criteria.min_area
        if criteria.city and criteria.city not in profile.preferred_cities:
            profile.preferred_cities.append(criteria.city)
        if criteria.preferences:
            profile.preferences = criteria.preferences
        self.repository.save_profile(profile)
        self.repository.add_interaction(
            user_id,
            "search",
            {
                "mode": mode,
                "city": criteria.city,
                "province": criteria.province,
                "budget": criteria.max_price,
                "min_area": criteria.min_area,
                "preferences": criteria.preferences,
                "raw_query": raw_query,
                "category": criteria.category,
            },
        )
        return self.repository.get_profile(user_id)

    def record_feedback(
        self, user_id: str, listing: Listing, status: str
    ) -> UserProfile:
        user_id = self.normalize_user_id(user_id)
        self.repository.save_feedback(
            user_id, listing.source, listing.external_id, status
        )
        self.repository.add_interaction(
            user_id,
            "property_feedback",
            {
                "source": listing.source,
                "external_id": listing.external_id,
                "status": status,
                "title": listing.title,
                "city": listing.city,
                "price": listing.price,
                "area": listing.area,
                "category": listing.category,
            },
        )
        return self.repository.get_profile(user_id)

    def remember_recommendations(
        self, user_id: str, listing_ids: list[str], parser: str
    ) -> None:
        self.repository.add_interaction(
            self.normalize_user_id(user_id),
            "recommendations",
            {"listing_ids": listing_ids, "parser": parser},
        )
