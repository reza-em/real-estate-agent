from typing import Protocol

from app.models.listing import Listing


class ListingProvider(Protocol):
    name: str
    categories: tuple[str, ...]

    def search(
        self, city: str, pages: int = 1, category: str = "property"
    ) -> list[Listing]: ...

    def close(self) -> None: ...
