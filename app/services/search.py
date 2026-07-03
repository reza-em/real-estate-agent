from __future__ import annotations

from collections.abc import Sequence

from app.db.repository import ListingRepository
from app.models.category import PROPERTY
from app.models.search import RankedListing, SearchCriteria, SearchResult
from app.providers.base import ListingProvider
from app.services.filtering import filter_listings
from app.services.geocoder import GeocoderService
from app.services.ranking import RankingService


class SearchService:
    def __init__(
        self,
        provider: ListingProvider | Sequence[ListingProvider],
        repository: ListingRepository,
        ranking: RankingService,
        geocoder: GeocoderService | None = None,
    ) -> None:
        self.providers = (
            list(provider)
            if isinstance(provider, Sequence) and not isinstance(provider, (str, bytes))
            else [provider]
        )
        self.repository = repository
        self.ranking = ranking
        self.geocoder = geocoder

    def search(self, criteria: SearchCriteria) -> SearchResult:
        fetched: list = []
        source_errors: dict[str, str] = {}
        for provider in self.providers:
            if criteria.category not in provider.categories:
                continue
            try:
                fetched.extend(
                    provider.search(criteria.city, criteria.pages, criteria.category)
                )
            except Exception as exc:
                source_errors[provider.name] = str(exc)
        fetched = list({(item.source, item.external_id): item for item in fetched}.values())
        filtered = filter_listings(fetched, criteria)
        if self.geocoder and criteria.category == PROPERTY:
            self.geocoder.enrich(filtered, criteria.city)
        self.repository.save(fetched)
        analyses = self.ranking.rank(
            filtered,
            criteria.max_price,
            criteria.preferences,
            criteria.use_ai,
        )
        self.repository.save_analyses(analyses)

        analysis_by_id = {item.external_id: item for item in analyses}
        ranked = [
            RankedListing(listing, analysis_by_id[listing.external_id])
            for listing in filtered
        ]
        ranked.sort(key=lambda item: item.analysis.score, reverse=True)
        return SearchResult(
            items=ranked,
            fetched_count=len(fetched),
            ai_requested=criteria.use_ai,
            ai_available=self.ranking.ai_available,
            city=criteria.city,
            category=criteria.category,
            source_errors=source_errors,
        )
