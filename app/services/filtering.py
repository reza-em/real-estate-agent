from app.models.listing import Listing
from app.models.search import SearchCriteria


def filter_listings(
    listings: list[Listing], criteria: SearchCriteria
) -> list[Listing]:
    filtered = []
    for listing in listings:
        if listing.price is None or listing.price > criteria.max_price:
            continue
        if criteria.min_area and (
            listing.area is None or listing.area < criteria.min_area
        ):
            continue
        filtered.append(listing)
    return filtered
