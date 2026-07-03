from pathlib import Path
import sqlite3

from app.db.repository import ListingRepository
from app.models.listing import Listing
from app.models.search import SearchCriteria
from app.services.filtering import filter_listings
from app.services.ranking import RankingService
from app.services.search import SearchService


def listing(external_id: str, price: int, area: int | None) -> Listing:
    return Listing("test", external_id, "خانه", price, "تهران", "https://example.com", area=area)


def test_filter_applies_budget_and_area():
    items = [
        listing("good", 8_000_000_000, 90),
        listing("small", 7_000_000_000, 60),
        listing("expensive", 12_000_000_000, 100),
    ]
    criteria = SearchCriteria("تهران", 10_000_000_000, min_area=80)
    assert [item.external_id for item in filter_listings(items, criteria)] == ["good"]


def test_basic_ranking_prefers_lower_price():
    items = [listing("a", 9_000_000_000, 80), listing("b", 7_000_000_000, 80)]
    analyses = RankingService(api_key="").rank(items, 10_000_000_000, use_ai=False)
    scores = {item.external_id: item.score for item in analyses}
    assert scores["b"] > scores["a"]


def test_repository_migrates_and_saves_area(tmp_path: Path):
    repository = ListingRepository(tmp_path / "test.db")
    repository.save([listing("a", 9_000_000_000, 85)])
    with repository.connect() as connection:
        row = connection.execute(
            "SELECT area FROM listings WHERE external_id = 'a'"
        ).fetchone()
    assert row["area"] == 85


def test_repository_migrates_existing_database_for_location(tmp_path: Path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE listings (
                source TEXT NOT NULL,
                external_id TEXT NOT NULL,
                title TEXT NOT NULL,
                price INTEGER,
                location TEXT,
                url TEXT NOT NULL,
                description TEXT,
                score REAL,
                analysis TEXT,
                raw_json TEXT,
                seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source, external_id)
            )
            """
        )
    repository = ListingRepository(path)
    with repository.connect() as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(listings)")
        }
    assert {"latitude", "longitude", "address", "city", "category"} <= columns


def test_search_service_orchestrates_provider_filter_and_repository(tmp_path: Path):
    class FakeProvider:
        name = "fake"
        categories = ("property",)

        def search(
            self, city: str, pages: int = 1, category: str = "property"
        ) -> list[Listing]:
            assert city == "تهران"
            assert pages == 2
            assert category == "property"
            return [
                listing("match", 8_000_000_000, 90),
                listing("over-budget", 11_000_000_000, 100),
            ]

    service = SearchService(
        FakeProvider(),
        ListingRepository(tmp_path / "search.db"),
        RankingService(api_key=""),
    )
    criteria = SearchCriteria(
        "تهران", 10_000_000_000, min_area=80, pages=2, use_ai=False
    )
    result = service.search(criteria)
    assert result.fetched_count == 2
    assert [item.listing.external_id for item in result.items] == ["match"]


def test_search_service_keeps_results_when_one_provider_fails(tmp_path: Path):
    class WorkingProvider:
        name = "working"
        categories = ("car",)

        def search(self, city, pages=1, category="property"):
            return [
                Listing(
                    "working",
                    "car-1",
                    "خودرو",
                    900_000_000,
                    city,
                    "https://example.com/car",
                    city=city,
                    category="car",
                )
            ]

    class FailingProvider:
        name = "offline"
        categories = ("car",)

        def search(self, city, pages=1, category="property"):
            raise RuntimeError("temporarily unavailable")

    service = SearchService(
        [FailingProvider(), WorkingProvider()],
        ListingRepository(tmp_path / "multi.db"),
        RankingService(api_key=""),
    )
    result = service.search(
        SearchCriteria("تهران", 1_000_000_000, category="car", use_ai=False)
    )
    assert [item.listing.external_id for item in result.items] == ["car-1"]
    assert result.source_errors == {"offline": "temporarily unavailable"}
