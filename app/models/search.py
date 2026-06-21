from __future__ import annotations

from dataclasses import dataclass, field

from app.models.analysis import Analysis
from app.models.listing import Listing


@dataclass(frozen=True, slots=True)
class SearchCriteria:
    city: str
    max_price: int
    min_area: int = 0
    pages: int = 1
    preferences: str = ""
    use_ai: bool = True
    province: str = ""
    city_id: str = ""


@dataclass(slots=True)
class RankedListing:
    listing: Listing
    analysis: Analysis


@dataclass(slots=True)
class SearchResult:
    items: list[RankedListing] = field(default_factory=list)
    fetched_count: int = 0
    ai_requested: bool = False
    ai_available: bool = False
    city: str = ""

    @property
    def best(self) -> RankedListing | None:
        return self.items[0] if self.items else None
