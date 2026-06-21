from __future__ import annotations

from app.db.repository import ListingRepository
from app.models.search import RankedListing, SearchCriteria, SearchResult
from app.providers.base import ListingProvider
from app.services.filtering import filter_listings
from app.services.geocoder import GeocoderService
from app.services.ranking import RankingService


class SearchService:
    def __init__(
        self,
        provider: ListingProvider,
        repository: ListingRepository,
        ranking: RankingService,
        geocoder: GeocoderService | None = None,
    ) -> None:
        self.provider = provider
        self.repository = repository
        self.ranking = ranking
        self.geocoder = geocoder

    def search(self, criteria: SearchCriteria) -> SearchResult:
        fetched = self.provider.search(criteria.city, criteria.pages)
        filtered = filter_listings(fetched, criteria)
        if self.geocoder:
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
        )
