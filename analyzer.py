"""Compatibility exports for code using the original module path."""

from dataclasses import asdict

from app.models.analysis import Analysis
from app.models.listing import Listing
from app.services.ranking import RankingService


def basic_analysis(listings: list[Listing], max_price: int) -> list[Analysis]:
    return RankingService._basic_rank(listings, max_price)


def analyze(
    listings: list[Listing], max_price: int, preferences: str = ""
) -> list[Analysis]:
    return RankingService().rank(listings, max_price, preferences, use_ai=True)


def to_dict(item: Analysis) -> dict[str, object]:
    return asdict(item)


__all__ = ["Analysis", "analyze", "basic_analysis", "to_dict"]
