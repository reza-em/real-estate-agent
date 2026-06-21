from typing import Protocol

from app.models.listing import Listing


class ListingProvider(Protocol):
    name: str

    def search(self, city: str, pages: int = 1) -> list[Listing]: ...
