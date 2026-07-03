from __future__ import annotations

from app.models.analysis import Analysis
from app.models.category import PROPERTY, category_label
from app.models.memory import UserProfile
from app.models.search import RankedListing, SearchCriteria


class DecisionEngine:
    """Produces explainable, deterministic scores from query and memory."""

    def rank(
        self,
        items: list[RankedListing],
        criteria: SearchCriteria,
        profile: UserProfile,
    ) -> list[RankedListing]:
        ranked = [self._score(item, criteria, profile) for item in items]
        ranked.sort(key=lambda item: item.analysis.score, reverse=True)
        return ranked

    def _score(
        self,
        item: RankedListing,
        criteria: SearchCriteria,
        profile: UserProfile,
    ) -> RankedListing:
        listing = item.listing
        price_score = self._price_score(listing.price, criteria.max_price)
        area_score = (
            self._area_score(listing.area, criteria.min_area)
            if criteria.category == PROPERTY
            else 18
        )
        location_score = self._location_score(
            listing.city, listing.location, criteria.city
        )
        history_score = self._history_score(listing.external_id, listing.city, listing.area, profile)
        total = max(0, min(100, price_score + area_score + location_score + history_score))

        reasons = []
        if price_score >= 25:
            reasons.append("قیمت با بودجه شما فاصله امنی دارد")
        else:
            reasons.append("قیمت در محدوده بودجه تعیین‌شده است")
        if criteria.min_area and listing.area and listing.area >= criteria.min_area:
            reasons.append(f"متراژ آن از حداقل {criteria.min_area} متر بیشتر است")
        if location_score == 20:
            reasons.append(f"در شهر موردنظر شما، {criteria.city}، قرار دارد")
        if listing.external_id in profile.liked_properties:
            reasons.append(f"این {category_label(criteria.category)} را قبلاً پسندیده‌اید")
        elif history_score >= 12 and profile.interaction_count:
            reasons.append("با الگوی جست‌وجوهای قبلی شما هماهنگ است")

        analysis = Analysis(
            external_id=listing.external_id,
            score=total,
            summary="؛ ".join(reasons) + ".",
            risks=item.analysis.risks,
            score_breakdown={
                "تطابق بودجه": price_score,
                "تطابق متراژ": area_score,
                "تطابق موقعیت": location_score,
                "حافظه و سابقه": history_score,
            },
        )
        return RankedListing(listing=listing, analysis=analysis)

    @staticmethod
    def _price_score(price: int | None, budget: int) -> int:
        if price is None or budget <= 0:
            return 5
        if price > budget:
            return 0
        ratio = price / budget
        return max(20, min(35, round(35 - ratio * 15)))

    @staticmethod
    def _area_score(area: int | None, minimum: int) -> int:
        if area is None:
            return 5
        if minimum <= 0:
            return 18
        if area < minimum:
            return max(0, round(15 * area / minimum))
        surplus = min((area - minimum) / max(minimum, 1), 1)
        return round(20 + 5 * surplus)

    @staticmethod
    def _location_score(city: str, location: str, preferred_city: str) -> int:
        return 20 if city == preferred_city or preferred_city in location else 5

    @staticmethod
    def _history_score(
        external_id: str,
        city: str,
        area: int | None,
        profile: UserProfile,
    ) -> int:
        if external_id in profile.rejected_properties:
            return -50
        if external_id in profile.liked_properties:
            return 20
        score = 5
        if city and city in profile.preferred_cities:
            score += 8
        if area and profile.min_area and area >= profile.min_area:
            score += 5
        return min(score, 18)
